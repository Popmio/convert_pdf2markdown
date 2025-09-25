
### 1. 安装依赖

#### 方法一：使用 uv（推荐）
```

uv venv
uv sync
```

#### 方法二：使用传统 pip

```bash
pip install -r requirements.txt
```

注意：Windows用户需要额外安装poppler，可从[这里](https://github.com/oschwartz10612/poppler-windows/releases/)下载。

详细的uv使用说明请查看 [UV_USAGE.md](UV_USAGE.md)。

### 2. 配置API密钥

编辑 `conf/conf.yaml` 文件，设置您的API密钥：

```yaml
model:
  apikey: "your-api-key-here"
```

### 3. 基本使用流程

#### 方式一：使用主程序（推荐）

```bash
# 注意：如果使用uv，请在命令前加 'uv run'
# 例如：uv run main.py full --create

# 创建PDF转图片任务（推荐）
python main.py pdf2img --create --input pdfs --output images

# 创建图片转Markdown任务（推荐）
python main.py img2md --create --input images --output markdowns

# 或者直接创建完整流程任务
python main.py full --create --input pdfs --output markdowns

# 运行任务（会返回任务ID）
python main.py run --task-id <task_id>

# 查看所有任务
python main.py list

# 查看任务状态
python main.py status --task-id <task_id>
```

#### 方式二：使用单独的转换脚本

```bash
# PDF转图片
python convert_pdf2img.py --create
python convert_pdf2img.py --task-id <task_id>

# 图片转Markdown
python convert_img2markdown.py --create
python convert_img2markdown.py --task-id <task_id>
```

## 高级功能

### 断点续传

当任务中断后，直接使用相同的任务ID重新运行即可：

```bash
python main.py run --task-id <task_id>
```

系统会自动跳过已完成的文件，继续处理未完成的部分。

### 从头重新处理

如果需要重新处理所有文件（不续传）：

```bash
python main.py run --task-id <task_id> --no-resume
```

### 语义分割

将长文档按语义分割成多个小文件：（试验）

```bash
# 按语义分割
python split_by_meaning.py markdowns/document.md --method semantic

# 按标题分割
python split_by_meaning.py markdowns/document.md --method headers

# 按长度分割
python split_by_meaning.py markdowns/document.md --method length --max-chars 3000
```

## 目录结构

```
convert_pdf2markdown/
├── conf/                   # 配置文件目录
│   ├── conf.yaml          # 主配置文件
│   └── prompts.yaml       # Prompt配置
├── pdfs/                  # PDF输入目录
├── images/                # 图片输出目录
├── markdowns/             # Markdown输出目录
├── tasks/                 # 任务状态文件目录
├── main.py                # 主程序入口
├── task_manager.py        # 任务管理器
├── convert_pdf2img.py     # PDF转图片
├── convert_img2markdown.py # 图片转Markdown
└── split_by_meaning.py    # 语义分割工具
```

## 配置说明

### conf/conf.yaml

- `model`: 模型配置（API地址、密钥、超时等）
- `pdf2img`: PDF转图片参数（DPI、质量等）
- `img2markdown`: 图片转Markdown参数（批次大小、请求延迟等）
- `task_manager`: 任务管理参数（更新间隔等）
- `paths`: 默认路径配置

### conf/prompts.yaml

- `img2markdown`: 图片转Markdown的提示词
- `split_by_meaning`: 语义分割的提示词

## 常见问题

### Q: 如何查看任务进度？

A: 使用 `python main.py status --task-id <task_id>` 查看详细进度。

### Q: 任务失败后如何处理？

A: 直接重新运行相同的任务ID，系统会自动续传。查看状态可以看到失败的文件列表。

### Q: 如何调整识别质量？

A: 编辑 `conf/prompts.yaml` 中的提示词，或调整 `conf/conf.yaml` 中的DPI等参数。

### Q: 支持哪些图片格式？

A: 目前支持JPG格式，PDF转换时会自动生成JPG图片。

## 编程接口

如需在代码中使用，参考 `example_usage.py`：

```python
from task_manager import TaskManager
from _types import TaskType

# 创建任务
task_manager = TaskManager()
task_id = task_manager.create_task(
    task_type=TaskType.pdf2image,
    input_path="pdfs",
    output_path="images"
)

# 运行任务
success = task_manager.start_task(
    task_id=task_id,
    process_callback=your_process_function,
    resume=True
)
```

## 注意事项

1. 首次运行前请确保已安装所有依赖
2. API调用有频率限制，可在配置中调整请求延迟
3. 大文件处理可能需要较长时间，请耐心等待
4. 任务状态文件保存在tasks目录，请勿手动修改
