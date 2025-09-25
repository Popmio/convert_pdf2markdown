import os
import argparse
import base64
from pathlib import Path
import time
from tqdm import tqdm
from typing import Optional
from openai import OpenAI

from task_manager import TaskManager
from _types import TaskType
from config_loader import config


class ImageToMarkdownConverter:
    
    def __init__(self):
        model_config = config.get_model_config()
        self.client = OpenAI(
            api_key=model_config.get('apikey'),
            base_url=model_config.get('url'),
        )
        self.model_name = model_config.get('name')
        self.img2md_config = config.get_img2markdown_config()
        self.prompts = config.prompts.get('img2markdown', {})
        
    def encode_image(self, image_path: str) -> str:

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def chat_img2markdown(self, image_path: str) -> str:

        try:
            base64_image = self.encode_image(image_path)
            
            # Get prompt from config
            user_prompt = self.prompts.get('user_prompt', 
                "请将图像内容转换为规范的格式纯文本，如果是空白页请输出“(空白页)”，不要包含任何解释或额外说明。")
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.prompts.get('system', '')
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )
            return completion.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"\n❌  处理失败 {Path(image_path).name}: {str(e)}")
            return self.prompts.get('error_prompt', '[识别失败]')
    
    def process_image_folder(self, folder_path: str, output_path: str) -> Optional[str]:

        folder_path = Path(folder_path)
        output_path = Path(output_path)

        jpg_files = sorted(
            folder_path.glob("*.jpg"), 
            key=lambda x: int(x.stem.split('_')[-1]) if '_' in x.stem and x.stem.split('_')[-1].isdigit() else 0
        )
        
        if not jpg_files:
            error_msg = f"子文件夹 {folder_path} 中没有找到 JPG 文件"
            print(f"\n⚠️  {error_msg}")
            return error_msg
        
        print(f"\n📁 处理文件夹: {folder_path.name} ({len(jpg_files)} 个图片)")
        
        markdown_contents = []
        start_time = time.time()
        delay = self.img2md_config.get('delay_between_requests', 0.5)

        for img_file in tqdm(jpg_files, desc=f"🖼️  {folder_path.name}", unit="页", leave=True):
            content = self.chat_img2markdown(str(img_file))
            if content and content != self.prompts.get('error_prompt', '[识别失败]'):
                markdown_contents.append(content)

            if delay > 0:
                time.sleep(delay)
        
        end_time = time.time()
        print(f"\n📁 文件夹耗时: {end_time - start_time:.2f} 秒")

        if markdown_contents:
            final_markdown = "\n\n".join(markdown_contents)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(final_markdown, encoding="utf-8")
            print(f"✅  已保存: {output_path}")
            return None
        else:
            error_msg = "没有成功识别任何图片"
            print(f"❌  {error_msg}")
            return error_msg


def main():
    parser = argparse.ArgumentParser(description='Convert images to markdown with task management')
    parser.add_argument('--create', action='store_true', help='Create a new task')
    parser.add_argument('--task-id', type=str, help='Task ID to run or resume')
    parser.add_argument('--input', type=str, help='Input directory path')
    parser.add_argument('--output', type=str, help='Output directory path')
    parser.add_argument('--list', action='store_true', help='List all tasks')
    parser.add_argument('--status', type=str, help='Get status of a specific task')
    parser.add_argument('--no-resume', action='store_true', help='Restart task from beginning')
    
    args = parser.parse_args()

    paths_config = config.get_paths_config()
    if not args.input:
        args.input = paths_config.get('image_output', 'images')
    if not args.output:
        args.output = paths_config.get('markdown_output', 'markdowns')

    task_manager = TaskManager()

    if args.list:
        tasks = task_manager.list_tasks()
        img2md_tasks = [t for t in tasks if t.get('task_type') == TaskType.img2markdown]
        
        if not img2md_tasks:
            print("📋 没有找到图片转Markdown的任务")
        else:
            print("📋 图片转Markdown任务列表：")
            for task in img2md_tasks:
                print(f"  ID: {task['task_id']}")
                print(f"  状态: {task['status']}")
                print(f"  进度: {task['processed_files']}/{task['total_files']} ({task['progress']*100:.1f}%)")
                print(f"  创建时间: {task['created_time']}")
                print()
        return

    if args.status:
        status = task_manager.get_task_status(args.status)
        if status:
            print(f"📊 任务状态：")
            print(f"  ID: {status['task_id']}")
            print(f"  状态: {status['status']}")
            print(f"  进度: {status['processed_files']}/{status['total_files']} ({status['progress']*100:.1f}%)")
            print(f"  失败文件: {status['failed_files']}")
            print(f"  创建时间: {status['created_time']}")
            if status['start_time']:
                print(f"  开始时间: {status['start_time']}")
            if status['end_time']:
                print(f"  结束时间: {status['end_time']}")
        else:
            print(f"❌ 任务 {args.status} 不存在")
        return

    if args.create:
        if not os.path.exists(args.input):
            print(f"❌ 输入目录不存在: {args.input}")
            return
            
        print(f"📁 输入目录: {args.input}")
        print(f"📁 输出目录: {args.output}")
        
        task_id = task_manager.create_task(
            task_type=TaskType.img2markdown,
            input_path=args.input,
            output_path=args.output
        )
        
        print(f"\n💡 使用以下命令运行任务：")
        print(f"   python convert_img2markdown.py --task-id {task_id}")
        return

    if args.task_id:
        print(f"🚀 运行任务: {args.task_id}")

        converter = ImageToMarkdownConverter()
        
        success = task_manager.start_task(
            task_id=args.task_id,
            process_callback=converter.process_image_folder,
            resume=not args.no_resume
        )
        
        if success:
            print(f"✅ 任务 {args.task_id} 完成!")
        else:
            print(f"⚠️ 任务 {args.task_id} 未完成")
        return

    parser.print_help()


if __name__ == "__main__":
    main()