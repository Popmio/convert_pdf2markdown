
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from openai import OpenAI

from config_loader import config


class SemanticSplitter:
    
    def __init__(self):
        model_config = config.get_model_config()
        self.client = OpenAI(
            api_key=model_config.get('apikey'),
            base_url=model_config.get('url'),
        )
        self.model_name = model_config.get('name')
        self.prompts = config.prompts.get('split_by_meaning', {})
        
    def analyze_document_structure(self, markdown_content: str) -> List[Dict[str, Any]]:

        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.prompts.get('system', '你是一个专业的文档分析助手。')
                    },
                    {
                        "role": "user",
                        "content": f"{self.prompts.get('user_prompt', '请分析文档结构')}\n\n文档内容：\n{markdown_content}"
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(completion.choices[0].message.content)
            return result.get('sections', [])
            
        except Exception as e:
            print(f"❌ 分析文档结构失败: {str(e)}")
            return []
    
    def split_by_headers(self, markdown_content: str, max_level: int = 2) -> List[Dict[str, Any]]:

        lines = markdown_content.split('\n')
        sections = []
        current_section = {
            'section_id': 0,
            'title': 'Introduction',
            'content': [],
            'start_line': 0,
            'level': 0
        }
        
        for i, line in enumerate(lines):

            if line.strip().startswith('#'):

                level = len(line.split()[0])
                if level <= max_level and line.strip() != '#':

                    if current_section['content']:
                        current_section['content'] = '\n'.join(current_section['content'])
                        current_section['end_line'] = i - 1
                        sections.append(current_section)
                    

                    current_section = {
                        'section_id': len(sections) + 1,
                        'title': line.strip().lstrip('#').strip(),
                        'content': [line],
                        'start_line': i,
                        'level': level
                    }
                else:
                    current_section['content'].append(line)
            else:
                current_section['content'].append(line)
        

        if current_section['content']:
            current_section['content'] = '\n'.join(current_section['content'])
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def split_by_length(self, markdown_content: str, max_chars: int = 3000) -> List[Dict[str, Any]]:

        paragraphs = markdown_content.split('\n\n')
        sections = []
        current_section = {
            'section_id': 1,
            'title': f'Section 1',
            'content': '',
            'start_line': 0
        }
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            

            if current_length + para_length > max_chars and current_section['content']:
                sections.append(current_section)
                current_section = {
                    'section_id': len(sections) + 2,
                    'title': f'Section {len(sections) + 2}',
                    'content': para,
                    'start_line': current_section.get('end_line', 0) + 1
                }
                current_length = para_length
            else:
                if current_section['content']:
                    current_section['content'] += '\n\n' + para
                else:
                    current_section['content'] = para
                current_length += para_length
        

        if current_section['content']:
            sections.append(current_section)
        
        return sections
    
    def merge_small_sections(self, sections: List[Dict[str, Any]], 
                           min_chars: int = 500) -> List[Dict[str, Any]]:

        if not sections:
            return sections
        
        merged = []
        current = sections[0]
        
        for section in sections[1:]:

            if len(current['content']) < min_chars:
                current['content'] += '\n\n' + section['content']
                current['end_line'] = section.get('end_line', current.get('end_line', 0))
                if 'title' in section and section['title']:
                    current['title'] += ' / ' + section['title']
            else:
                merged.append(current)
                current = section

        merged.append(current)

        for i, section in enumerate(merged):
            section['section_id'] = i + 1
        
        return merged
    
    def save_sections(self, sections: List[Dict[str, Any]], 
                     output_dir: Path, base_name: str):

        output_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            'base_name': base_name,
            'total_sections': len(sections),
            'sections': []
        }
        
        for section in sections:

            section_num = str(section['section_id']).zfill(3)
            title_slug = section.get('title', 'section').lower()
            title_slug = ''.join(c if c.isalnum() or c in '-_' else '_' for c in title_slug)[:50]
            filename = f"{base_name}_{section_num}_{title_slug}.md"

            output_path = output_dir / filename
            output_path.write_text(section['content'], encoding='utf-8')

            metadata['sections'].append({
                'section_id': section['section_id'],
                'title': section.get('title', ''),
                'filename': filename,
                'chars': len(section['content']),
                'start_line': section.get('start_line', 0),
                'end_line': section.get('end_line', 0)
            })
            
            print(f"✅ 保存: {filename} ({len(section['content'])} 字符)")

        metadata_path = output_dir / f"{base_name}_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"\n📊 元数据已保存: {metadata_path}")


def main():
    parser = argparse.ArgumentParser(description='Split markdown documents by semantic meaning')
    parser.add_argument('input', type=str, help='Input markdown file or directory')
    parser.add_argument('--output', type=str, help='Output directory (default: input_dir/split)')
    parser.add_argument('--method', type=str, 
                       choices=['semantic', 'headers', 'length', 'auto'],
                       default='auto',
                       help='Split method (default: auto)')
    parser.add_argument('--max-chars', type=int, default=3000,
                       help='Maximum characters per section for length split')
    parser.add_argument('--min-chars', type=int, default=500,
                       help='Minimum characters per section (merge smaller)')
    parser.add_argument('--max-header-level', type=int, default=2,
                       help='Maximum header level for header split')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入路径不存在: {args.input}")
        return

    splitter = SemanticSplitter()

    if input_path.is_file():
        markdown_files = [input_path]
        default_output = input_path.parent / 'split'
    else:
        markdown_files = list(input_path.glob('**/*.md'))
        default_output = input_path / 'split'
    
    output_dir = Path(args.output) if args.output else default_output
    
    print(f"📂 找到 {len(markdown_files)} 个Markdown文件")
    
    for md_file in markdown_files:
        print(f"\n📄 处理: {md_file}")

        content = md_file.read_text(encoding='utf-8')

        if args.method == 'semantic' or (args.method == 'auto' and len(content) < 50000):
            print("  🧠 使用语义分割...")
            sections = splitter.analyze_document_structure(content)
            if not sections:
                print("  ⚠️ 语义分割失败，改用标题分割")
                sections = splitter.split_by_headers(content, args.max_header_level)
                
        elif args.method == 'headers':
            print("  📑 使用标题分割...")
            sections = splitter.split_by_headers(content, args.max_header_level)
            
        elif args.method == 'length':
            print("  📏 使用长度分割...")
            sections = splitter.split_by_length(content, args.max_chars)
            
        else:  # auto
            print("  🔄 自动选择分割方式...")

            sections = splitter.split_by_headers(content, args.max_header_level)

            if len(sections) < 2 or len(sections) > 50:
                sections = splitter.split_by_length(content, args.max_chars)

        if args.min_chars > 0:
            original_count = len(sections)
            sections = splitter.merge_small_sections(sections, args.min_chars)
            if len(sections) < original_count:
                print(f"  🔗 合并小节: {original_count} → {len(sections)}")

        base_name = md_file.stem
        splitter.save_sections(sections, output_dir, base_name)
        
        print(f"  ✅ 完成！生成 {len(sections)} 个文件")
    
    print(f"\n🎉 全部完成！输出目录: {output_dir}")


if __name__ == "__main__":
    main()
