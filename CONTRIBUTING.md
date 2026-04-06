# 贡献指南

首先，感谢你对 **Ledom Photo Organizer** 的关注和贡献！🙏

本文档提供了贡献该项目的方式和规范。

---

## 📋 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [报告 Bug](#报告-bug)
- [提交功能建议](#提交功能建议)
- [提交代码](#提交代码)
- [代码规范](#代码规范)
- [提交消息规范](#提交消息规范)
- [许可证](#许可证)

---

## 行为准则

### 我们的承诺

为了促进开放和友好的环境，我们承诺：

- 欢迎不同背景和身份的参与者
- 创建安全、友好的讨论氛围
- 尊重不同的观点和意见
- 接受建设性的批评

### 不可接受的行为

以下行为不被接受：

- 骚扰、歧视、诽谤
- 发布他人隐私信息
- 明显的不诚实行为
- 其他可能被合理认定为不适当的行为

---

## 如何贡献

贡献有多种方式：

### 🐛 报告 Bug
- [创建 Issue](#报告-bug)
- 提供详细的复现步骤
- 包含环境信息

### 💡 建议功能
- [创建 Discussion 或 Issue](#提交功能建议)
- 详细说明使用场景
- 等待社区反馈

### 📚 改进文档
- 修正拼写错误
- 补充缺失说明
- 翻译文档

### 🔧 提交代码
- Bug 修复
- 新功能实现
- 性能优化
- 代码重构

---

## 报告 Bug

### 重要须知
- 请先查阅 [README](README.md) 和 [CHANGELOG](CHANGELOG.md)
- 搜索已有 Issues，避免重复报告
- 提供尽可能详细的信息帮助我们快速定位问题

### Bug 报告模板

创建 Issue 时，请包含以下信息：

```markdown
## 描述问题
简洁地描述这个 Bug

## 复现步骤
1. 步骤一
2. 步骤二
3. ...

## 预期行为
应该发生什么

## 实际行为
实际发生了什么

## 环境信息
- 操作系统: [e.g. Windows 11, macOS 13, Ubuntu 22.04]
- Python 版本: [e.g. 3.8, 3.10, 3.11]
- 本项目版本: [e.g. 1.9.4]
- 依赖版本:
  - streamlit: x.x.x
  - exifread: x.x.x
  - 其他: x.x.x

## 错误日志
粘贴完整的错误信息或日志

## 截图（如适用）
添加截图帮助解释问题
```

---

## 提交功能建议

### 重要须知
- 功能建议应该是通用的，而不仅针对个人使用场景
- 请考虑实现的复杂性和维护成本
- 查看现有 Issues，避免建议重复功能

### 功能建议模板

```markdown
## 功能描述
清晰简明地描述建议的功能

## 使用场景
为什么需要这个功能？什么场景下会用到？

## 当前解决方案
目前如何处理这个需求（如果有的话）

## 建议的实现
（可选）你认为如何实现这个功能

## 其他
任何其他信息，如参考链接、示意图等
```

---

## 提交代码

### 开始前的准备

1. **Fork 本仓库**
   - 访问项目页面，点击 "Fork" 按钮

2. **克隆你的 Fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/photo-organizer.git
   cd photo-organizer
   ```

3. **添加上游仓库**
   ```bash
   git remote add upstream https://github.com/Ledom/photo-organizer.git
   ```

4. **创建虚拟环境**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

### 修改代码

1. **同步最新代码**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **创建功能分支**
   ```bash
   git checkout -b fix/issue-123
   # 或
   git checkout -b feature/new-feature
   ```

3. **进行修改**
   - 遵循 [代码规范](#代码规范)
   - 添加必要的注释
   - 确保代码可读性

4. **测试你的改动**
   ```bash
   streamlit run photo_organizer_streamlit.py
   ```

### 提交代码

1. **提交更改**
   ```bash
   git add .
   git commit -m "fix: 修复 EXIF 日期提取失败的问题

   - 修改 get_exif_date 函数
   - 添加了时间戳容错处理
   - 通过测试用例验证
   "
   ```

2. **推送分支**
   ```bash
   git push origin fix/issue-123
   ```

3. **创建 Pull Request**
   - 访问你的 Fork，点击 "Compare & pull request"
   - 填写 PR 标题和描述
   - 链接相关的 Issue（如有）
   - 等待 Review

### Pull Request 检查清单

提交前确保：

- [ ] 代码符合项目代码规范
- [ ] 添加了必要的注释和文档字符串
- [ ] 在本地测试过改动
- [ ] 提交消息清晰明确
- [ ] 没有引入新的依赖（除非必需）
- [ ] 代码没有 print 调试语句
- [ ] 更新了相关文档

---

## 代码规范

### Python 风格

遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 编码风格：

```python
# ✅ 好的例子
def extract_date_from_exif(file_path):
    """
    从 EXIF 中提取日期信息。
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        datetime.datetime: 提取的日期，如果失败返回 None
    """
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f)
            # ...
    except Exception as e:
        logging.error(f"Failed to extract EXIF: {e}")
        return None


# ❌ 避免的例子
def extractDate(filePath):  # 不遵循命名规范
    x = exifread.process_file(open(filePath))  # 没有错误处理
    # ...
```

### 注释规范

```python
# ✅ 好的注释
# 快速检查文件是否为照片
if file_ext.lower() in SUPPORTED_FORMATS:
    process_file(file)

# ❌ 避免的注释
# 检查
if file_ext.lower() in SUPPORTED_FORMATS:  # 检查扩展名
    process_file(file)  # 处理文件
```

### 函数文档

```python
def copy_with_atomic_operation(src, dst):
    """
    原子化复制文件。
    
    如果复制失败，自动回滚，确保源文件完整。
    
    Args:
        src (str): 源文件路径
        dst (str): 目标文件路径
        
    Returns:
        bool: 复制成功返回 True，否则 False
        
    Raises:
        IOError: 如果源文件不存在或没有读权限
        
    Example:
        >>> copy_with_atomic_operation('/source/photo.jpg', '/dest/photo.jpg')
        True
    """
    # 实现...
```

### 变量命名

```python
# ✅ 清晰的名称
source_directory = "/path/to/photos"
total_files_processed = 0
is_dry_run_mode = True
supported_formats = ['jpg', 'png', 'heic']

# ❌ 避免
src_dir = "/path/to/photos"
cnt = 0
d = True
formats = ['jpg', 'png', 'heic']
```

---

## 提交消息规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

- **fix**: Bug 修复
- **feat**: 新功能
- **perf**: 性能改进
- **refactor**: 代码重构
- **docs**: 文档改进
- **test**: 测试相关
- **chore**: 工具或配置改动

### 示例

```bash
# 修复 Bug
git commit -m "fix: 修复 EXIF 时间戳解析失败

修改 get_exif_date 函数，增加对多种日期格式的支持。
修复了当 EXIF 中缺少时区信息时的崩溃问题。

Closes #123"

# 新功能
git commit -m "feat: 支持 AVIF 格式

添加 AVIF 格式识别和处理。
更新 SUPPORTED_FORMATS 列表。"

# 性能优化
git commit -m "perf: 优化 MD5 哈希计算

使用分块读取大文件，减少内存占用。
性能提升 30%。"
```

---

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。

---

## 需要帮助？

- 📧 **邮件**: liuwei71320@gmail.com
- 🐙 **Issues**: [GitHub Issues](https://github.com/Ledom/photo-organizer/issues)
- 💬 **讨论**: [GitHub Discussions](https://github.com/Ledom/photo-organizer/discussions)

---

感谢你的贡献！🌟
