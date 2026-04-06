# 更新日志 (Changelog)

所有值得注意的本项目变化都会在此文件中记录。

格式参考 [Keep a Changelog](https://keepachangelog.com/)

---

## [1.9.4] - 2026-04-06

### ✨ 新增
- **DRY-RUN 模式** - 预览效果，确认无误后再执行，100% 安全
- **智能去重功能** - 基于 MD5 哈希校验，自动跳过已处理文件
- **断点续传支持** - SQLite 状态库，中断后可继续，重复运行自动跳过

### 🐛 修复
- 修复 `start_processing` 提前返回 `None` 导致的崩溃
- 修复 dry-run 模式创建真实目录和数据库的问题
- 修复 overwrite 冲突模式的原子化问题（先写临时文件，成功后再替换）
- 修复 Fast-Hash 与全量 MD5 哈希前缀冲突
- 修复 `get_filename_date` 正则顺序问题
- 修复数据库连接泄漏（添加 `StateDB.close()` 方法）

### ⚡ 性能改进
- **速度提升 10 倍** - Fast-Hash 采样算法 + 4线程并发
- 优化线程池调度，减少上下文切换
- 改进内存管理，支持万级文件处理
- WAL 模式数据库，提升并发写入性能

### 🔒 安全加固
- **原子化操作** - 复制/移动失败自动回滚，绝不丢失源文件
- 路径遍历防御，防止目录跳出攻击
- Magic Number 校验，防止伪造文件类型
- 权限检查和符号链接检测

### 📖 文档改进
- 完善 Web 界面使用说明
- 添加配置参数详解
- 补充常见问题 FAQ

### 🤝 联合开发
感谢以下 AI 模型的联合开发：
- **DeepSeek** - 架构设计、并发模型、Fast-Hash 算法
- **Gemini** - 性能优化、内存管理、数据库优化
- **Qwen** - 安全加固、防御机制、原子化操作
- **Claude** - 稳定性增强、异常处理、边界条件覆盖

---

## [1.9.0] - 2026-03-01

### ✨ 新增
- **初始版本发布** 🎉
- Streamlit Web 界面，零配置启动
- 支持 JPEG/PNG/HEIC/RAW/MP4 等 20+ 文件格式
- **智能日期提取** - EXIF → 文件名 → mtime 三级降级
- 多种目录结构支持（设备/年/月 / 年/月 / 年/月/日 等）
- 复制/移动/跳过三种冲突处理策略
- Windows .bat 一键启动脚本

### 🎯 实测数据
- 2,104 张照片实测稳定，耗时 ~15 分钟
- 平均处理速度 2.4 张/秒（4线程）
- 预估 8000 张照片 SSD + 8线程：6-8 张/秒

---

## [1.0.0] - 2025-12-15

### ✨ 新增
- 核心照片整理引擎
- 命令行版本
- 基础 EXIF 支持

---

## 版本规范说明

- **主版本号** - 大功能更新或不兼容改动
- **次版本号** - 新增功能（向后兼容）
- **修订版本号** - Bug 修复、小改进

### 标签说明
- ✨ **New Feature** - 新功能
- 🐛 **Bug Fix** - Bug 修复
- ⚡ **Performance** - 性能改进
- 🔒 **Security** - 安全修复
- 📖 **Documentation** - 文档改进
- ♻️ **Refactor** - 代码重构
- 🎨 **Style** - 代码风格（不影响功能）
- ✅ **Test** - 测试相关

---

## 安装特定版本

```bash
# 安装最新版本
pip install -r requirements.txt

# 如果支持 pip 安装（未来规划）
pip install ledom-photo-organizer==1.9.4
```

---

## 反馈与建议

- 🐛 **报告 Bug** - [GitHub Issues](https://github.com/Ledom/photo-organizer/issues)
- 💡 **功能建议** - [GitHub Discussions](https://github.com/Ledom/photo-organizer/discussions)
- 📧 **直接联系** - liuwei71320@gmail.com
