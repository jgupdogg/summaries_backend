import json
from datetime import date, datetime
from summary_func import * 
from vectors import *
from prompts import *
import re

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

class Article:
    def __init__(self, title, content, date_str, site_key, **kwargs):
        self.title = title
        self.content = content
        self.date = self._parse_date(date_str)
        self.additional_info = kwargs
        self.summary = None
        self.keywords = None
        self.dense_vector = None
        self.sparse_vector = None
        self.symbol = site_key
        self.id = self._generate_id()
        self.ai_generated_title = None

    def _generate_id(self):
        if isinstance(self.date, date):
            formatted_date = self.date.strftime("%Y%m%d")
        else:
            formatted_date = "00000000"  # Default if date is invalid
        return f"{self.symbol}_{formatted_date}"

    def _parse_date(self, date_str):
        if not isinstance(date_str, str):
            print(f"Invalid date_str: {date_str} (type: {type(date_str)})")
            return date_str
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return date_str

    def __repr__(self):
        return f"Article('{self.title}', date: {self.date}, id: {self.id})"

    def __str__(self):
        return f"{self.title}\n\nDate: {self.date}\nID: {self.id}\n\n{self.content[:100]}..."

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'title': self.title,
            'ai_generated_title': self.ai_generated_title,
            'content': self.content,
            'date': self.date.isoformat() if isinstance(self.date, date) else self.date,
            'summary': self.summary,
            'keywords': self.keywords,
            **self.additional_info
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
    
    def map_summary(self):
        """Generates and stores the summary of the article."""
        raw_summary = map_summary(self)
        # Split the title and summary
        parts = raw_summary.split('\n', 1)
        if len(parts) > 1:
            self.ai_generated_title = parts[0].replace('Title: ', '').strip()
            self.summary = parts[1].strip()
        else:
            self.summary = raw_summary
        return self.summary
    
    def generate_keywords(self):
        """Creates keywords to be used for sparse vector generation"""
        prompt = generate_keywords_prompt(self)
        raw_keywords = call_openai(prompt)
        # Clean up the keywords
        self.keywords = [
            re.sub(r'^\d+\.\s*', '', word.strip())  # Remove leading numbers and dots
            for word in raw_keywords.split('\n')
            if word.strip()
        ]
        return self.keywords

    def generate_dense_vector(self):
        """Generates and stores the dense vector representation of the summary."""
        self.dense_vector = create_dense_vector(self.summary)
        return self.dense_vector

    def generate_sparse_vector(self):
        """Generates and stores the sparse vector representation of the keywords."""
        if self.summary is None:
            print('no summary')
            self.generate_summary()
        self.sparse_vector = create_sparse_vector(self.keywords)
        return self.sparse_vector
    
    def generate_all_representations(self):
        """Generates summary, keywords, dense vector, and sparse vector in the correct order."""
        self.map_summary()
        print(self.summary)
        self.generate_keywords()
        print(self.keywords)
        self.generate_dense_vector()
        print(f'len dense: {len(self.dense_vector)}')
        self.generate_sparse_vector()
        print(f'sparse: {self.sparse_vector}')
        return {
            'summary': self.summary,
            'keywords': self.keywords,
            'dense_vector': self.dense_vector,
            'sparse_vector': self.sparse_vector
        }

    def upsert_to_pinecone(self):
        return upsert_to_pinecone(self)

    @classmethod
    def from_dict(cls, data):
        title = data.pop('title', '')
        content = data.pop('content', '')
        date_str = data.pop('date', '')
        site_key = data.pop('symbol', '')
        return cls(title, content, date_str, site_key, **data)
    
    
    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls.from_dict(data)

    def add_info(self, key, value):
        self.additional_info[key] = value