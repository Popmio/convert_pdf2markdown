# 使用 uv 运行项目

本项目完全支持使用 `uv` 作为包管理工具。`uv` 是一个快速的Python包管理器，比传统的pip快10-100倍。

## 安装 uv

如果还没有安装 uv，请先安装：

## 项目设置

### 1. 创建虚拟环境并安装依赖

```bash
# 进入项目目录
cd convert_pdf2markdown

# 创建虚拟环境
uv venv

# 激活虚拟环境 (Windows)
.venv\Scripts\activate

# 激活虚拟环境 (macOS/Linux)
source .venv/bin/activate

# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 或者使用 pyproject.toml 安装
uv pip install -e .
```

### 2. 同步依赖（推荐）

使用 uv 的同步功能自动管理依赖：

```bash
# 同步项目依赖
uv sync

# 包含开发依赖
uv sync --dev
```

## 运行项目

### 使用 uv run（无需激活虚拟环境）

```bash
# 主程序
uv run python main.py --help

# 创建任务
uv run python main.py full --create --input pdfs --output markdowns

# 运行任务
uv run python main.py run --task-id <task_id>

# 查看任务列表
uv run python main.py list

# 查看任务状态
uv run python main.py status --task-id <task_id>
```

### 分步转换

```bash
# PDF 转图片
uv run python convert_pdf2img.py --create
uv run python convert_pdf2img.py --task-id <task_id>

# 图片转 Markdown
uv run python convert_img2markdown.py --create
uv run python convert_img2markdown.py --task-id <task_id>

# 语义分割
uv run python split_by_meaning.py markdowns/document.md
```

## 使用项目脚本

如果使用 `pyproject.toml` 安装，可以直接运行定义的脚本：

```bash
# 安装项目
uv pip install -e .

# 运行脚本
uv run pdf2markdown full --create
uv run pdf2img --create
uv run img2md --create
uv run split-docs markdowns/document.md
```

## 依赖管理

### 添加新依赖

```bash
# 添加运行时依赖
uv pip install package_name
uv pip freeze > requirements.txt

# 添加开发依赖
uv pip install --dev pytest black ruff
```

### 更新依赖

```bash
# 更新所有依赖
uv pip install -U -r requirements.txt

# 更新特定包
uv pip install -U openai
```

### 锁定依赖版本

```bash
# 生成锁文件
uv pip freeze > requirements.lock

# 从锁文件安装
uv pip install -r requirements.lock
```

## 开发工作流

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/convert_pdf2markdown.git
cd convert_pdf2markdown
```

### 2. 设置开发环境

```bash
# 创建并同步环境
uv venv
uv sync --dev

# 或一步完成
uv sync --dev --refresh
```

### 3. 运行测试（如果有）

```bash
uv run pytest
```

### 4. 代码格式化

```bash
# 使用 black 格式化
uv run black .

# 使用 ruff 检查
uv run ruff check .
```

## Docker 支持（可选）

创建一个使用 uv 的 Dockerfile：

```dockerfile
FROM python:3.11-slim

# 安装 uv
RUN pip install uv

WORKDIR /app

# 复制项目文件
COPY . .

# 安装依赖
RUN uv venv && uv pip install -r requirements.txt

# 运行应用
CMD ["uv", "run", "python", "main.py"]
```

## 常见问题

### Q: uv 和 pip 有什么区别？

A: uv 是 pip 的快速替代品，速度快10-100倍，且提供更好的依赖解析。

### Q: 可以同时使用 uv 和 pip 吗？

A: 可以，但建议统一使用 uv 以避免依赖冲突。

### Q: 如何切换Python版本？

A: 编辑 `.python-version` 文件，然后重新创建虚拟环境：
```bash
echo "3.12" > .python-version
uv venv --python 3.12
```

### Q: Windows 上 uv 遇到权限问题？

A: 以管理员身份运行 PowerShell，或使用：
```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 性能优化提示

1. **使用 uv 缓存**：uv 自动缓存下载的包，无需额外配置

2. **并行安装**：uv 默认并行下载和安装包

3. **本地索引**：对于企业环境，可以配置本地PyPI镜像：
```bash
uv pip install -i https://your-mirror.com/simple package_name
```

## 使用 Makefile（最简单）

如果您的系统支持 make 命令，可以使用提供的 Makefile 快速操作：

```bash
# 快速开始（安装依赖并设置项目）
make quick-start

# 创建任务
make create-full   # 创建完整流程任务
make create-pdf    # 创建PDF转图片任务
make create-img    # 创建图片转Markdown任务

# 运行任务
make run ID=<task_id>

# 查看任务
make list                # 列出所有任务
make status ID=<task_id> # 查看任务状态

# 清理
make clean         # 清理临时文件
make clean-tasks   # 清理任务文件
```

## 更多信息

- uv 官方文档：https://github.com/astral-sh/uv
- 项目主文档：[README.md](README.md)
- 中文使用说明：[使用说明.md](使用说明.md)
