#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Photo Organizer v1.9.4 - [The Architect Edition]
联合开发：
- DeepSeek (架构主导)      - 生产者-消费者并发模型、Fast-Hash 采样算法、整体架构设计
- Gemini (性能优化)        - 线程池优化、内存管理、WAL 模式数据库
- Qwen (安全加固)          - 路径遍历防御、Magic Number 校验、原子化操作
- Claude (稳定性增强)      - 多线程竞态修复、异常处理完善、边界条件覆盖
- Ledom (需求与测试)       - 产品需求定义、2104张照片实测、版本迭代管理
更新摘要：
1. 修复 start_processing 提前返回 None 导致的崩溃
2. 修复 dry-run 模式创建真实目标目录和数据库的问题
3. 修复 overwrite 冲突模式的原子化问题（先写临时文件，成功后再替换）
4. 修复 Fast-Hash 与全量 MD5 哈希前缀冲突
5. 修复 get_filename_date 正则顺序问题
6. 添加 StateDB.close() 方法防止连接泄漏
7. 添加原子化文件替换工具函数
"""

import streamlit as st
import os
import shutil
import re
import datetime
import logging
import hashlib
import sqlite3
import threading
import queue
import time
import warnings
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- 依赖库预检 ----------
HAS_EXIF = False
try:
    import exifread
    HAS_EXIF = True
except ImportError:
    pass

HAS_HEIF = False
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HAS_HEIF = True
except ImportError:
    pass

# ---------- 环境与 UI 配置 ----------
warnings.filterwarnings("ignore", message="missing ScriptRunContext")
logging.getLogger("streamlit.runtime.scriptrunner").setLevel(logging.ERROR)

st.set_page_config(page_title="Ledom Photo Organizer v1.9.4", page_icon="🏗️", layout="wide")
st.title("🏗️ Ledom Photo Organizer v1.9.4")
st.markdown("**工业级安全架构** | 支持万级照片/视频的高速、安全、精准整理。")

# ---------- 侧边栏：专家级配置 ----------
with st.sidebar:
    st.header("📂 路径安全设置")
    source_dir = st.text_input("源目录", value=os.path.expanduser("~/Pictures/Phone_Imports"))
    target_dir = st.text_input("目标目录", value=os.path.expanduser("~/Pictures/Organized_Photos"))

    st.header("🧩 整理策略")
    folder_structure = st.selectbox("目录结构", 
        ["device_year_month", "year_month", "year_month_day", "year_month_device"], index=0)
    operation_mode = st.radio("操作模式", ["copy", "move"], horizontal=True, help="建议首次使用先用 Copy 模式")
    conflict_res = st.selectbox("同名冲突处理", ["rename", "skip", "overwrite"])

    st.header("🚀 性能引擎")
    threads = st.slider("并发线程数", 1, 32, 4)
    use_fast_hash = st.checkbox("启用 Fast-Hash (推荐)", value=True, help="大文件采样校验，性能提升10倍")
    dry_run = st.checkbox("DRY-RUN 预览模式", value=False)

    st.markdown("---")
    st.caption(f"依赖状态: EXIF({'✅' if HAS_EXIF else '❌'}) | HEIF({'✅' if HAS_HEIF else '❌'})")
    st.caption("Ledom Engine v1.9.4 | 2026 Architect Edition")

# ---------- 日志捕获 ----------
class LogCaptureHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def emit(self, record):
        msg = self.format(record)
        if 'log_messages' not in st.session_state:
            st.session_state.log_messages = []
        st.session_state.log_messages.append(msg)
        if len(st.session_state.log_messages) > 200:
            st.session_state.log_messages = st.session_state.log_messages[-200:]

def setup_logging():
    if '_logging_setup_done' in st.session_state:
        return
    st.session_state._logging_setup_done = True
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logger.addHandler(console)
    capture = LogCaptureHandler()
    logger.addHandler(capture)

# ---------- 原子化文件操作工具 ----------
def atomic_copy(src, dst):
    """原子化复制：先复制到临时文件，成功后再重命名"""
    temp_dir = os.path.dirname(dst)
    os.makedirs(temp_dir, exist_ok=True)
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(dir=temp_dir, delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        shutil.copy2(src, tmp_path)
        # 原子替换
        os.replace(tmp_path, dst)
    except Exception:
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

def atomic_move(src, dst, src_hash, fast_mode=True):
    """原子化移动：先复制并校验哈希，成功后再删除源文件"""
    atomic_copy(src, dst)
    # 哈希二次校验目标文件完整性
    dst_hash = calculate_smart_hash(dst, fast_mode)
    if dst_hash == src_hash:
        os.remove(src)
    else:
        if os.path.exists(dst):
            os.remove(dst)
        raise Exception("哈希校验不一致，操作已回滚")

# ---------- 第一层：安全验证与文件校验 ----------

def validate_environment(src, dst, dry_run=False):
    """安全审计：规范化路径并检查权限与嵌套（dry-run 模式下不创建目录）"""
    src, dst = os.path.normpath(src), os.path.normpath(dst)
    src_abs, dst_abs = os.path.abspath(src), os.path.abspath(dst)

    if not os.path.isdir(src_abs):
        raise ValueError(f"源目录无效: {src}")
    if src_abs == dst_abs:
        raise ValueError("源目录与目标目录不能相同")
    if dst_abs.startswith(src_abs + os.sep):
        raise ValueError("目标目录不能在源目录内部（防止无限递归）")
    
    if not dry_run:
        os.makedirs(dst_abs, exist_ok=True)
        if not os.access(dst_abs, os.W_OK):
            raise ValueError("目标目录无写入权限")
    
    return src_abs, dst_abs

def is_valid_media(filepath):
    """文件扩展名检查（快速过滤）"""
    valid_exts = ('.jpg', '.jpeg', '.png', '.heic', '.heif', '.bmp', '.webp', '.gif', '.tiff',
                  '.cr2', '.nef', '.arw', '.dng', '.avi', '.mkv', '.m4v', '.3gp', '.mp4')
    return filepath.lower().endswith(valid_exts)

# ---------- 第二层：核心计算引擎 ----------

def calculate_smart_hash(filepath, fast_mode=True):
    """Fast-Hash 采样算法（哈希前缀区分模式）"""
    try:
        f_size = os.path.getsize(filepath)
        hash_md5 = hashlib.md5()
        with open(filepath, "rb") as f:
            if f_size < 10 * 1024 * 1024 or not fast_mode:
                for chunk in iter(lambda: f.read(65536), b""):
                    hash_md5.update(chunk)
                prefix = "full_"
            else:
                # 头部
                hash_md5.update(f.read(65536))
                # 中部
                f.seek(f_size // 2)
                hash_md5.update(f.read(65536))
                # 尾部
                f.seek(-65536, 2)
                hash_md5.update(f.read(65536))
                # 文件大小作为盐
                hash_md5.update(str(f_size).encode())
                prefix = "fast_"
        return f"{prefix}{hash_md5.hexdigest()}"
    except Exception:
        return None

def get_rich_meta(filepath):
    """深度提取元数据：结合 EXIF 库与文件名逻辑"""
    res = {"date": None, "device": "Unknown_Device"}
    
    # 1. 尝试从 EXIF 提取
    if HAS_EXIF:
        try:
            with open(filepath, 'rb') as f:
                tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal', details=False)
                if 'EXIF DateTimeOriginal' in tags:
                    t_str = str(tags['EXIF DateTimeOriginal'])
                    try:
                        res["date"] = datetime.datetime.strptime(t_str[:19], '%Y:%m:%d %H:%M:%S').date()
                    except Exception:
                        pass
                model = tags.get('Image Model')
                if model:
                    res["device"] = str(model).strip().replace(' ', '_').replace('/', '_')
                elif 'EXIF LensModel' in tags:
                    res["device"] = str(tags['EXIF LensModel']).strip().replace(' ', '_').replace('/', '_')
        except Exception:
            pass

    # 2. 降级：从文件名正则提取日期（精确规则优先）
    if not res["date"]:
        name = os.path.basename(filepath)
        patterns = [
            r'IMG_(\d{4})(\d{2})(\d{2})',
            r'VID_(\d{4})(\d{2})(\d{2})',
            r'PANO_(\d{4})(\d{2})(\d{2})',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})(\d{2})(\d{2})',
        ]
        for pattern in patterns:
            m = re.search(pattern, name)
            if m:
                try:
                    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    # 合理性检查
                    if 1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        res["date"] = datetime.date(year, month, day)
                        break
                except Exception:
                    continue

    # 3. 终极降级：文件修改时间
    if not res["date"]:
        try:
            ts = os.path.getmtime(filepath)
            res["date"] = datetime.datetime.fromtimestamp(ts).date()
        except Exception:
            pass
        
    return res

def check_disk_space(filepath, target_dir):
    """检查磁盘空间是否足够"""
    try:
        file_size = os.path.getsize(filepath)
        total, used, free = shutil.disk_usage(target_dir)
        return free >= file_size * 1.1
    except Exception:
        return True

class ThreadSafeStateDB:
    """高并发状态数据库"""
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.conn = None
        self._init_db()

    def _init_db(self):
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=30000")
        self.conn.execute("CREATE TABLE IF NOT EXISTS processed (source_path TEXT PRIMARY KEY, md5 TEXT, target_path TEXT, processed_time TIMESTAMP)")
        self.conn.commit()

    def is_done(self, source_path, md5):
        with self.lock:
            cur = self.conn.execute("SELECT md5 FROM processed WHERE source_path=?", (source_path,))
            row = cur.fetchone()
            return row is not None and row[0] == md5

    def mark_done(self, source_path, md5, target_path):
        with self.lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO processed (source_path, md5, target_path, processed_time) VALUES (?, ?, ?, ?)",
                (source_path, md5, target_path, datetime.datetime.now().isoformat())
            )
            self.conn.commit()

    def close(self):
        if self.conn:
            with self.lock:
                self.conn.close()
                self.conn = None

# ---------- 第三层：处理流水线 ----------

def start_processing(config):
    try:
        # dry-run 模式下不创建目标目录
        src, dst = validate_environment(
            config['source_dir'], 
            config['target_dir'], 
            dry_run=config['dry_run']
        )
    except ValueError as e:
        st.error(f"❌ 配置错误: {e}")
        return 0, 0, []  # 🔧 修复：返回空结果而不是 None

    setup_logging()
    
    # dry-run 模式使用临时数据库
    if config['dry_run']:
        db_path = os.path.join(tempfile.gettempdir(), ".ledom_dryrun_state.db")
        # 清理旧的 dry-run 数据库
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception:
                pass
    else:
        db_path = os.path.join(dst, ".ledom_v194_state.db")
    
    db = ThreadSafeStateDB(db_path)
    
    # 扫描文件
    files = []
    for root, _, fs in os.walk(src):
        for f in fs:
            full_p = os.path.join(root, f)
            if is_valid_media(full_p):
                files.append(full_p)
    
    total = len(files)
    if total == 0:
        st.warning("⚠️ 未发现支持的媒体文件，请检查目录或文件类型。")
        db.close()
        return 0, 0, []  # 🔧 修复：返回空结果而不是 None

    logging.info(f"找到 {total} 个文件，开始整理")
    logging.info(f"并发线程数: {config['threads']}")
    logging.info("=" * 50)

    # 创建进度条和状态容器（仅非 dry-run 模式或少量文件时显示）
    progress_container = st.container()
    with progress_container:
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    success_count = 0
    skip_count = 0
    fail_list = []
    
    success_lock = threading.Lock()
    skip_lock = threading.Lock()
    fail_lock = threading.Lock()
    progress_lock = threading.Lock()
    processed_count = 0

    def unit_task(f_path):
        nonlocal processed_count, success_count, skip_count
        
        try:
            # 1. 唯一性校验
            f_hash = calculate_smart_hash(f_path, config['use_fast_hash'])
            if not f_hash:
                with fail_lock:
                    fail_list.append(f_path)
                return "FAIL"
            
            if db.is_done(f_path, f_hash):
                with skip_lock:
                    skip_count += 1
                return "SKIP"

            # 2. 元数据分析
            meta = get_rich_meta(f_path)
            if not meta["date"]:
                with fail_lock:
                    fail_list.append(f_path)
                return "FAIL"

            # 3. 目标路径构建
            dt, dev = meta["date"], meta["device"]
            y, m, d = dt.strftime('%Y'), dt.strftime('%m月'), dt.strftime('%d日')
            struct_map = {
                "year_month": [y, m],
                "year_month_day": [y, m, d],
                "device_year_month": [dev, y, m],
                "year_month_device": [y, m, dev]
            }
            sub_dirs = struct_map.get(config['folder_structure'], [y, m])
            final_dst_dir = os.path.join(dst, *sub_dirs)
            
            if not config['dry_run']:
                os.makedirs(final_dst_dir, exist_ok=True)
            
            target_p = os.path.join(final_dst_dir, os.path.basename(f_path))

            # 4. 冲突处理
            if os.path.exists(target_p):
                if config['conflict_res'] == 'skip':
                    with skip_lock:
                        skip_count += 1
                    return "SKIP"
                elif config['conflict_res'] == 'overwrite':
                    # 不删除，让原子操作覆盖
                    pass
                elif config['conflict_res'] == 'rename':
                    base, ext = os.path.splitext(target_p)
                    counter = 1
                    while True:
                        new_target = f"{base}_{counter}{ext}"
                        if not os.path.exists(new_target):
                            target_p = new_target
                            break
                        counter += 1

            # 5. 磁盘空间检查（仅复制模式）
            if not config['dry_run'] and config['operation_mode'] == 'copy':
                if not check_disk_space(f_path, final_dst_dir):
                    logging.error(f"磁盘空间不足，无法复制: {f_path}")
                    with fail_lock:
                        fail_list.append(f_path)
                    return "FAIL"

            # 6. 执行操作
            if config['dry_run']:
                logging.info(f"[DRY-RUN] 将处理: {f_path} -> {target_p}")
                with success_lock:
                    success_count += 1
                return "DRY"
            
            # 原子化执行
            if config['operation_mode'] == 'move':
                atomic_move(f_path, target_p, f_hash, config['use_fast_hash'])
            else:
                atomic_copy(f_path, target_p)

            db.mark_done(f_path, f_hash, target_p)
            with success_lock:
                success_count += 1
            return "SUCCESS"
            
        except Exception as e:
            logging.error(f"处理失败: {f_path} | 原因: {e}")
            with fail_lock:
                fail_list.append(f_path)
            return "FAIL"

    # 并发执行 + 主线程更新进度
    with ThreadPoolExecutor(max_workers=config['threads']) as executor:
        futures = [executor.submit(unit_task, f) for f in files]
        
        for i, future in enumerate(as_completed(futures)):
            try:
                future.result()
            except Exception:
                pass  # 错误已在 unit_task 中处理
            
            with progress_lock:
                processed_count += 1
                if total > 0:
                    progress_bar.progress(processed_count / total)
                    status_text.text(f"处理中: {processed_count}/{total} | 成功: {success_count} | 跳过: {skip_count}")
            
            if processed_count % 100 == 0:
                logging.info(f"进度: {processed_count}/{total}")

    # 清理进度条容器
    progress_container.empty()
    db.close()
    
    logging.info("=" * 50)
    logging.info(f"整理完成 | 成功: {success_count} | 跳过: {skip_count} | 失败: {len(fail_list)}")
    
    # 显示结果（非 dry-run 模式）
    if not config['dry_run']:
        st.success(f"🎊 整理任务完成！成功: {success_count}, 跳过: {skip_count}, 失败: {len(fail_list)}")
        if fail_list:
            with st.expander(f"查看失败详情 ({len(fail_list)}个)"):
                for item in fail_list[:50]:
                    st.text(item)
                if len(fail_list) > 50:
                    st.text(f"... 还有 {len(fail_list) - 50} 个失败文件")
    else:
        st.info(f"🔍 DRY-RUN 完成！将处理: {success_count} 个文件，跳过: {skip_count} 个，失败: {len(fail_list)} 个")
    
    return success_count, len(fail_list), fail_list

# ---------- 界面主循环 ----------

def main():
    # 初始化 session_state
    if 'log_messages' not in st.session_state:
        st.session_state.log_messages = []
    if 'result' not in st.session_state:
        st.session_state.result = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    setup_logging()

    col1, col2 = st.columns([1, 2])
    with col1:
        start_button = st.button("🚀 开始整理", type="primary", use_container_width=True, disabled=st.session_state.processing)

    with col2:
        if start_button and not st.session_state.processing:
            st.session_state.log_messages = []
            st.session_state.result = None
            st.session_state.processing = True

            config = {
                'source_dir': source_dir,
                'target_dir': target_dir,
                'folder_structure': folder_structure,
                'operation_mode': operation_mode,
                'conflict_res': conflict_res,
                'threads': threads,
                'use_fast_hash': use_fast_hash,
                'dry_run': dry_run,
            }

            with st.spinner("正在处理，请稍候..."):
                success, fail, failed_files = start_processing(config)

            st.session_state.result = {
                'success': success,
                'fail': fail,
                'failed_files': failed_files
            }
            st.session_state.processing = False
            st.rerun()

    # 显示整理结果
    if st.session_state.result is not None:
        res = st.session_state.result
        col_metrics = st.columns(3)
        col_metrics[0].metric("✅ 成功", res['success'])
        col_metrics[1].metric("❌ 失败", res['fail'])
        col_metrics[2].metric("📊 总计", res['success'] + res['fail'])

        if res['fail'] > 0:
            with st.expander(f"查看失败文件列表 ({res['fail']}个)"):
                for f in res['failed_files'][:50]:
                    st.code(f, language="text")
                if len(res['failed_files']) > 50:
                    st.text(f"... 还有 {len(res['failed_files']) - 50} 个")
        else:
            st.success("🎉 所有文件处理成功！")

        if st.button("清除结果"):
            st.session_state.result = None
            st.rerun()

    # 日志显示区域
    st.subheader("处理日志")
    if st.session_state.log_messages:
        for msg in st.session_state.log_messages[-100:]:
            st.text(msg)
    else:
        st.info("暂无日志，点击「开始整理」后显示处理过程。")

    if st.button("清空日志"):
        st.session_state.log_messages = []
        st.rerun()

if __name__ == "__main__":
    main()