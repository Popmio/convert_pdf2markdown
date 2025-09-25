import yaml
from pathlib import Path
from typing import Dict, Any
import os

class ConfigLoader:

    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf")
        self.config_dir = Path(config_dir)
        self._config = {}
        self._prompts = {}
        self._load_configs()
    
    def _load_configs(self):

        config_path = self.config_dir / "conf.yaml"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)

        prompts_path = self.config_dir / "prompts.yaml"
        if prompts_path.exists():
            with open(prompts_path, 'r', encoding='utf-8') as f:
                self._prompts = yaml.safe_load(f)
    
    @property
    def config(self) -> Dict[str, Any]:

        return self._config
    
    @property
    def prompts(self) -> Dict[str, Any]:

        return self._prompts
    
    def get_model_config(self) -> Dict[str, Any]:

        return self._config.get('model', {})
    
    def get_pdf2img_config(self) -> Dict[str, Any]:

        return self._config.get('pdf2img', {})
    
    def get_img2markdown_config(self) -> Dict[str, Any]:

        return self._config.get('img2markdown', {})
    
    def get_task_manager_config(self) -> Dict[str, Any]:

        return self._config.get('task_manager', {})
    
    def get_paths_config(self) -> Dict[str, Any]:

        return self._config.get('paths', {})
    
    def get_prompt(self, task_type: str, prompt_type: str) -> str:

        task_prompts = self._prompts.get(task_type, {})
        return task_prompts.get(prompt_type, "")
    
    def reload(self):

        self._load_configs()

# Global config instance
config = ConfigLoader()
