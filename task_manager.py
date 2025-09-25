import json
import os
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from datetime import datetime
import threading
import time
from _types import (
    TaskType, TaskStatus, FileStatus, 
    TaskInfo, FileRecord
)
from config_loader import config


class TaskManager:


    def __init__(self):
        self.config = config.get_task_manager_config()
        self.tasks_dir = Path(self.config.get('tasks_dir', 'tasks'))
        self.tasks_dir.mkdir(exist_ok=True)
        self.current_task: Optional[TaskInfo] = None
        self._status_update_thread = None
        self._stop_status_update = False
        
    def create_task(self, 
                    task_type: TaskType,
                    input_path: str,
                    output_path: str,
                    config_overrides: Dict[str, Any] = None) -> str:

        task_info = TaskInfo(
            task_type=task_type,
            input_path=input_path,
            output_path=output_path,
            config=config_overrides or {}
        )
        

        task_info.files = self._scan_input_files(task_type, input_path)
        task_info.total_files = len(task_info.files)
        

        self._save_task(task_info)
        
        print(f"✅ Created task {task_info.task_id} with {task_info.total_files} files")
        return task_info.task_id
    
    def load_task(self, task_id: str) -> Optional[TaskInfo]:

        task_file = self.tasks_dir / f"{self.config.get('task_file_prefix', 'task_')}{task_id}.json"
        if not task_file.exists():
            print(f"❌ Task {task_id} not found")
            return None
        
        with open(task_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            for field in ['created_time', 'start_time', 'end_time']:
                if data.get(field):
                    data[field] = datetime.fromisoformat(data[field])
            

            files = {}
            for file_path, record_data in data.get('files', {}).items():
                for field in ['start_time', 'end_time']:
                    if record_data.get(field):
                        record_data[field] = datetime.fromisoformat(record_data[field])
                files[file_path] = FileRecord(**record_data)
            data['files'] = files
            
            return TaskInfo(**data)
    
    def start_task(self, task_id: str, 
                   process_callback: Callable[[str, str], Optional[str]],
                   resume: bool = True) -> bool:

        self.current_task = self.load_task(task_id)
        if not self.current_task:
            return False
        

        self.current_task.status = TaskStatus.running
        if not self.current_task.start_time:
            self.current_task.start_time = datetime.now()
        

        self._start_status_update()
        
        try:

            for file_path, file_record in self.current_task.files.items():

                if resume and file_record.status == FileStatus.completed:
                    continue
                

                file_record.status = FileStatus.processing
                file_record.start_time = datetime.now()
                self._save_task(self.current_task)
                
                try:

                    output_path = self._generate_output_path(
                        file_path, 
                        self.current_task.input_path,
                        self.current_task.output_path,
                        self.current_task.task_type
                    )
                    

                    error_msg = process_callback(file_path, output_path)
                    
                    if error_msg:
                        file_record.status = FileStatus.failed
                        file_record.error_message = error_msg
                        self.current_task.failed_files += 1
                    else:
                        file_record.status = FileStatus.completed
                        file_record.output_path = output_path
                        self.current_task.processed_files += 1
                    
                except Exception as e:
                    file_record.status = FileStatus.failed
                    file_record.error_message = str(e)
                    self.current_task.failed_files += 1
                
                finally:
                    file_record.end_time = datetime.now()
                    self._save_task(self.current_task)
            

            self.current_task.status = TaskStatus.completed
            self.current_task.end_time = datetime.now()
            self._save_task(self.current_task)
            
            return True
            
        except KeyboardInterrupt:
            print("\n⚠️ Task interrupted by user")
            self.current_task.status = TaskStatus.paused
            self._save_task(self.current_task)
            return False
            
        except Exception as e:
            print(f"\n❌ Task failed: {str(e)}")
            self.current_task.status = TaskStatus.failed
            self.current_task.error_message = str(e)
            self._save_task(self.current_task)
            return False
            
        finally:
            self._stop_status_update_thread()
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:

        task = self.load_task(task_id)
        if not task:
            return None
        
        return {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status,
            'total_files': task.total_files,
            'processed_files': task.processed_files,
            'failed_files': task.failed_files,
            'progress': task.processed_files / task.total_files if task.total_files > 0 else 0,
            'created_time': task.created_time,
            'start_time': task.start_time,
            'end_time': task.end_time
        }
    
    def list_tasks(self) -> List[Dict[str, Any]]:

        tasks = []
        for task_file in self.tasks_dir.glob(f"{self.config.get('task_file_prefix', 'task_')}*.json"):
            task_id = task_file.stem.replace(self.config.get('task_file_prefix', 'task_'), '')
            status = self.get_task_status(task_id)
            if status:
                tasks.append(status)
        return sorted(tasks, key=lambda x: x['created_time'], reverse=True)
    
    def cancel_task(self, task_id: str) -> bool:

        task = self.load_task(task_id)
        if not task:
            return False
        
        task.status = TaskStatus.cancelled
        self._save_task(task)
        return True
    
    def _scan_input_files(self, task_type: TaskType, input_path: str) -> Dict[str, FileRecord]:

        files = {}
        input_path = Path(input_path)
        
        if task_type == TaskType.pdf2image:

            for pdf_file in input_path.rglob("*.pdf"):
                files[str(pdf_file)] = FileRecord(file_path=str(pdf_file))
                
        elif task_type == TaskType.img2markdown:

            for jpg_file in input_path.rglob("*.jpg"):
                folder = str(jpg_file.parent)
                if folder not in files:
                    files[folder] = FileRecord(file_path=folder)
                    
        elif task_type == TaskType.full_pipeline:

            for pdf_file in input_path.rglob("*.pdf"):
                files[str(pdf_file)] = FileRecord(file_path=str(pdf_file))
        
        return files
    
    def _generate_output_path(self, input_file: str, input_root: str, 
                             output_root: str, task_type: TaskType) -> str:

        input_path = Path(input_file)
        input_root = Path(input_root)
        output_root = Path(output_root)

        try:
            rel_path = input_path.relative_to(input_root)
        except ValueError:
            rel_path = input_path.name
        
        if task_type == TaskType.pdf2image:

            output_path = output_root / rel_path.parent / input_path.stem
            
        elif task_type == TaskType.img2markdown:

            folder_name = input_path.name.replace('：', '_')
            parent_name = input_path.parent.name.replace('：', '_')
            output_path = output_root / parent_name / f"{folder_name}.md"
            
        elif task_type == TaskType.full_pipeline:

            output_path = output_root / rel_path.parent / f"{input_path.stem}.md"
            
        else:
            output_path = output_root / rel_path
        
        return str(output_path)
    
    def _save_task(self, task: TaskInfo):

        task_file = self.tasks_dir / f"{self.config.get('task_file_prefix', 'task_')}{task.task_id}.json"

        task_dict = task.dict()

        for field in ['created_time', 'start_time', 'end_time']:
            if task_dict.get(field):
                task_dict[field] = task_dict[field].isoformat()

        files_dict = {}
        for file_path, record in task_dict['files'].items():
            record_dict = record
            for field in ['start_time', 'end_time']:
                if record_dict.get(field):
                    record_dict[field] = record_dict[field].isoformat()
            files_dict[file_path] = record_dict
        task_dict['files'] = files_dict
        
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(task_dict, f, ensure_ascii=False, indent=2)
    
    def _start_status_update(self):
        self._stop_status_update = False
        self._status_update_thread = threading.Thread(
            target=self._status_update_worker,
            daemon=True
        )
        self._status_update_thread.start()
    
    def _stop_status_update_thread(self):
        self._stop_status_update = True
        if self._status_update_thread:
            self._status_update_thread.join()
    
    def _status_update_worker(self):
        interval = self.config.get('status_update_interval', 5)
        while not self._stop_status_update:
            time.sleep(interval)
            if self.current_task:
                self._save_task(self.current_task)




