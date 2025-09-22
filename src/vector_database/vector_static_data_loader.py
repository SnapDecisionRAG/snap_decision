import hashlib
import re
from pathlib import Path
from datetime import datetime
from src.config import VECTOR_DATA_DIR

class VectorStaticDataLoader():
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.data_dir = VECTOR_DATA_DIR
        self.documents = []

        self.load_all_data()

    def load_all_data(self):
        print("Starting vector database static data loading process...")

        files = [
            'general_draft_strategy.md',
            'rules_and_settings.md', 
            'season_long_tips.md',
            'weather_impacts.md'
        ]

        for file in files:
            path = self.data_dir / file
            if path.exists():
                print(f"Processing {file} ...")
                self.process_file(path)
            else:
                print(f"Warning: {file} not found, skipping")

        if self.documents:
            self.db_manager.add_documents(self.documents)
        else:
            print("No documents to load")

        print("Vector database static data loading complete")

    def process_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            doc_name = path.stem

            sections = self.chunk_by_headers(content)
            for section in sections:
                if section['content'].strip():
                    id = self.generate_doc_id(doc_name, section['title'])

                    doc = {
                        'id': id,
                        'content': section['content'],
                        'metadata': {
                            'content_type': doc_name,
                            'section_title': section['title'],
                            'header_level': section['level'],
                            'source_file': str(path),
                            'timestamp': datetime.now().isoformat(),
                            'static_content': True
                        }
                    }

                    self.documents.append(doc)

        except Exception as e:
            print(f"Error processing {path}: {e}")

    def chunk_by_headers(self, content):
        sections = []
        header_pattern = r'^(#{1,6})\s+(.+?)$'
        lines = content.split("\n")

        current_section = {
            'title': 'Introduction',
            'level': 0,
            'content': '',
        }

        for line in lines:
            header_match = re.match(header_pattern, line.strip())
            if header_match:
                if current_section['content'].strip():
                    cleaned_content = self.clean_content(current_section['content'])
                    if cleaned_content.strip():
                        current_section['content'] = cleaned_content
                        sections.append(current_section)

                header_level = len(header_match.group(1))
                header_title = header_match.group(2).strip()

                current_section = {
                    'title': header_title,
                    'level': header_level,
                    'content': '',
                }

            else:
                current_section['content'] += f"{line}\n"

        if current_section['content'].strip():
            cleaned_content = self.clean_content(current_section['content'])
            if cleaned_content.strip():
                current_section['content'] = cleaned_content
                sections.append(current_section)

        return sections

    def generate_doc_id(self, doc_name, section_title):
        content_string = f"{doc_name}::{section_title}"
        hash_object = hashlib.md5(content_string.encode())
        return f"{doc_name}_{hash_object.hexdigest()[:8]}"
    
    def clean_content(self, content):
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Convert markdown formatting to readable text
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        
        # Remove markdown links but keep the text: [text](url) -> text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        
        # Clean up list formatting - keep bullets but normalize
        content = re.sub(r'^\s*[-*+]\s+', '• ', content, flags=re.MULTILINE)
        
        # Clean up numbered lists
        content = re.sub(r'^\s*\d+\.\s+', '', content, flags=re.MULTILINE)
        
        # Remove code blocks (if any)
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        content = re.sub(r'`([^`]+)`', r'\1', content)
        
        return content.strip()

    def reset_vector_database(self):
        print("Resetting vector database...")
        self.db_manager.reset_collection()
        self.documents = []
        self.load_all_data()
