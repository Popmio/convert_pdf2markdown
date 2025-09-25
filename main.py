
import argparse
import sys
from pathlib import Path
from typing import Optional

from task_manager import TaskManager
from _types import TaskType, TaskStatus
from config_loader import config
from convert_pdf2img import convert_pdf_to_jpg
from convert_img2markdown import ImageToMarkdownConverter


class PipelineManager:
    
    def __init__(self):
        self.task_manager = TaskManager()
        self.img_converter = ImageToMarkdownConverter()
        self.paths_config = config.get_paths_config()
        
    def run_full_pipeline(self, pdf_path: str, final_output: str) -> Optional[str]:

        pdf_path = Path(pdf_path)
        print(pdf_path)
        # Step 1
        temp_image_dir = Path(self.paths_config['image_output']) / pdf_path.parent.name / pdf_path.stem
        error = convert_pdf_to_jpg(str(pdf_path), str(temp_image_dir))
        if error:
            return f"PDF转图片失败: {error}"
        
        # Step 2
        error = self.img_converter.process_image_folder(str(temp_image_dir), final_output)
        if error:
            return f"图片转Markdown失败: {error}"
        
        return None


def main():
    parser = argparse.ArgumentParser(
        description='PDF to Markdown Converter - 支持任务管理和断点续传',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 创建PDF转图片任务
  python main.py pdf2img --create --input pdfs --output images
  
  # 创建图片转Markdown任务
  python main.py img2md --create --input images --output markdowns
  
  # 创建完整流程任务（PDF直接转Markdown）
  python main.py full --create --input pdfs --output markdowns
  
  # 运行任务
  python main.py run --task-id <task_id>
  
  # 查看所有任务
  python main.py list
  
  # 查看任务状态
  python main.py status --task-id <task_id>
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')

    pdf2img_parser = subparsers.add_parser('pdf2img', help='PDF转图片任务')
    pdf2img_parser.add_argument('--create', action='store_true', help='创建新任务')
    pdf2img_parser.add_argument('--input', type=str, help='输入目录')
    pdf2img_parser.add_argument('--output', type=str, help='输出目录')

    img2md_parser = subparsers.add_parser('img2md', help='图片转Markdown任务')
    img2md_parser.add_argument('--create', action='store_true', help='创建新任务')
    img2md_parser.add_argument('--input', type=str, help='输入目录')
    img2md_parser.add_argument('--output', type=str, help='输出目录')

    full_parser = subparsers.add_parser('full', help='完整流程任务（PDF直接转Markdown）')
    full_parser.add_argument('--create', action='store_true', help='创建新任务')
    full_parser.add_argument('--input', type=str, help='输入目录')
    full_parser.add_argument('--output', type=str, help='输出目录')

    run_parser = subparsers.add_parser('run', help='运行任务')
    run_parser.add_argument('--task-id', type=str, required=True, help='任务ID')
    run_parser.add_argument('--no-resume', action='store_true', help='从头开始，不续传')

    list_parser = subparsers.add_parser('list', help='列出所有任务')
    list_parser.add_argument('--type', type=str, choices=['pdf2image', 'img2markdown', 'full_pipeline'], 
                           help='只显示特定类型的任务')

    status_parser = subparsers.add_parser('status', help='查看任务状态')
    status_parser.add_argument('--task-id', type=str, required=True, help='任务ID')

    cancel_parser = subparsers.add_parser('cancel', help='取消任务')
    cancel_parser.add_argument('--task-id', type=str, required=True, help='任务ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    paths_config = config.get_paths_config()

    task_manager = TaskManager()
    pipeline_manager = PipelineManager()

    if args.command == 'pdf2img':
        if args.create:
            input_path = args.input or paths_config['pdf_input']
            output_path = args.output or paths_config['image_output']
            
            print(f"📁 输入目录: {input_path}")
            print(f"📁 输出目录: {output_path}")
            
            task_id = task_manager.create_task(
                task_type=TaskType.pdf2image,
                input_path=input_path,
                output_path=output_path
            )
            
            print(f"\n💡 使用以下命令运行任务：")
            print(f"   python main.py run --task-id {task_id}")
    
    elif args.command == 'img2md':
        if args.create:
            input_path = args.input or paths_config['image_output']
            output_path = args.output or paths_config['markdown_output']
            
            print(f"📁 输入目录: {input_path}")
            print(f"📁 输出目录: {output_path}")
            
            task_id = task_manager.create_task(
                task_type=TaskType.img2markdown,
                input_path=input_path,
                output_path=output_path
            )
            
            print(f"\n💡 使用以下命令运行任务：")
            print(f"   python main.py run --task-id {task_id}")
    
    elif args.command == 'full':
        if args.create:
            input_path = args.input or paths_config['pdf_input']
            output_path = args.output or paths_config['markdown_output']
            
            print(f"📁 输入目录: {input_path}")
            print(f"📁 输出目录: {output_path}")
            
            task_id = task_manager.create_task(
                task_type=TaskType.full_pipeline,
                input_path=input_path,
                output_path=output_path
            )
            
            print(f"\n💡 使用以下命令运行任务：")
            print(f"   python main.py run --task-id {task_id}")
    
    elif args.command == 'run':

        task = task_manager.load_task(args.task_id)
        if not task:
            print(f"❌ 任务 {args.task_id} 不存在")
            return
        
        print(f"🚀 运行任务: {args.task_id} (类型: {task.task_type})")
        

        if task.task_type == TaskType.pdf2image:
            callback = convert_pdf_to_jpg
        elif task.task_type == TaskType.img2markdown:
            callback = pipeline_manager.img_converter.process_image_folder
        elif task.task_type == TaskType.full_pipeline:
            callback = pipeline_manager.run_full_pipeline
        else:
            print(f"❌ 未知的任务类型: {task.task_type}")
            return
        
        success = task_manager.start_task(
            task_id=args.task_id,
            process_callback=callback,
            resume=not args.no_resume
        )
        
        if success:
            print(f"✅ 任务 {args.task_id} 完成!")
        else:
            print(f"⚠️ 任务 {args.task_id} 未完成")
    
    elif args.command == 'list':
        tasks = task_manager.list_tasks()
        

        if args.type:
            tasks = [t for t in tasks if t.get('task_type') == args.type]
        
        if not tasks:
            print("📋 没有找到任何任务")
        else:
            print("📋 任务列表：")
            print("-" * 80)

            for task_type in [TaskType.pdf2image, TaskType.img2markdown, TaskType.full_pipeline]:
                type_tasks = [t for t in tasks if t.get('task_type') == task_type]
                if type_tasks:
                    print(f"\n【{task_type.value}】")
                    for task in type_tasks:
                        status_icon = {
                            'created': '🆕',
                            'running': '🏃',
                            'paused': '⏸️',
                            'completed': '✅',
                            'failed': '❌',
                            'cancelled': '🚫'
                        }.get(task['status'], '❓')
                        
                        print(f"  {status_icon} {task['task_id'][:8]}... | "
                              f"进度: {task['processed_files']}/{task['total_files']} "
                              f"({task['progress']*100:.1f}%) | "
                              f"创建: {task['created_time'].strftime('%Y-%m-%d %H:%M')}")
    
    elif args.command == 'status':
        status = task_manager.get_task_status(args.task_id)
        if status:
            print(f"📊 任务详细状态：")
            print(f"  任务ID: {status['task_id']}")
            print(f"  状态: {status['status']}")
            print(f"  总文件数: {status['total_files']}")
            print(f"  已处理: {status['processed_files']}")
            print(f"  失败: {status['failed_files']}")
            print(f"  进度: {status['progress']*100:.1f}%")
            print(f"  创建时间: {status['created_time']}")
            if status['start_time']:
                print(f"  开始时间: {status['start_time']}")
            if status['end_time']:
                print(f"  结束时间: {status['end_time']}")

            task = task_manager.load_task(args.task_id)
            if task and task.failed_files > 0:
                print("\n  失败文件列表:")
                for file_path, record in task.files.items():
                    if record.status == 'failed':
                        print(f"    - {Path(file_path).name}: {record.error_message}")
        else:
            print(f"❌ 任务 {args.task_id} 不存在")
    
    elif args.command == 'cancel':
        if task_manager.cancel_task(args.task_id):
            print(f"🚫 任务 {args.task_id} 已取消")
        else:
            print(f"❌ 无法取消任务 {args.task_id}")


if __name__ == "__main__":
    main()
