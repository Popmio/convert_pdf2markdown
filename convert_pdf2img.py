import os
import argparse
from pathlib import Path
from pdf2image import convert_from_path
from typing import Optional

from task_manager import TaskManager
from _types import TaskType
from config_loader import config


def convert_pdf_to_jpg(pdf_path: str, output_folder: str) -> Optional[str]:

    pdf_config = config.get_pdf2img_config()
    
    pdf_path = Path(pdf_path)
    output_folder = Path(output_folder)
    
    print(f"📄 正在处理: {pdf_path.name}")

    output_folder.mkdir(parents=True, exist_ok=True)
    
    try:
        images = convert_from_path(
            str(pdf_path),
            dpi=pdf_config.get('dpi', 200),
            fmt=pdf_config.get('format', 'jpeg'),
            thread_count=pdf_config.get('thread_count', 4),
            poppler_path=pdf_config.get('poppler_path', None)
        )
        
        for i, img in enumerate(images):
            page_num = i + 1
            jpg_path = output_folder / f"page_{page_num:03d}.jpg"
            img.save(jpg_path, "JPEG", quality=pdf_config.get('quality', 95))
            print(f"  ✅ 保存第 {page_num} 页 → {jpg_path.name}")
        
        print(f"🎉 完成！共 {len(images)} 页\n")
        return None
        
    except Exception as e:
        error_msg = f"处理失败: {str(e)}"
        print(f"❌ {error_msg}\n")
        return error_msg


def main():
    parser = argparse.ArgumentParser(description='Convert PDF files to images with task management')
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
        args.input = paths_config.get('pdf_input', 'pdfs')
    if not args.output:
        args.output = paths_config.get('image_output', 'images')

    task_manager = TaskManager()

    if args.list:
        tasks = task_manager.list_tasks()
        if not tasks:
            print("📋 没有找到任何任务")
        else:
            print("📋 任务列表：")
            for task in tasks:
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
            task_type=TaskType.pdf2image,
            input_path=args.input,
            output_path=args.output
        )
        
        print(f"\n💡 使用以下命令运行任务：")
        print(f"   python convert_pdf2img.py --task-id {task_id}")
        return

    if args.task_id:
        print(f"🚀 运行任务: {args.task_id}")
        
        success = task_manager.start_task(
            task_id=args.task_id,
            process_callback=convert_pdf_to_jpg,
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
