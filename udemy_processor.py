import base64
import requests
from typing import List, Dict
from data_storage import DataStorage
from base_processor import SourceProcessor
from config import UDEMY_SECRET_KEY, UDEMY_CLIENT_ID
from datetime import datetime

class UdemyProcessor(SourceProcessor):
    BASE_URL = "https://www.udemy.com/api-2.0/courses/"
    COURSE_URL_PREFIX = "https://www.udemy.com"
    AVG_RATING_THRESHOLD = 4  
    DAYS_THRESHOLD = 365

    def __init__(self, platform_name="Udemy"):
        credentials = f"{UDEMY_CLIENT_ID}:{UDEMY_SECRET_KEY}"
        self.encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        super().__init__(platform_name)

    def fetch_source_items(self, query: str, limit: int) -> List[dict]:
        params = {
            "search": query,
            "page_size": limit*5,
            "ordering": "relevance",
            'fields[course]': 'created,avg_rating,title,updated,num_subscribers,url'
        }
        headers = {
            "Authorization": f"Basic {self.encoded_credentials}",
            "Accept": "application/json",
        }

        response = requests.get(self.BASE_URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve courses: {response.status_code}")
            return []

        return response.json().get("results", [])

    def filter_low_quality_sources(self, sources: List[dict]) -> List[dict]:
        filtered_sources = []
        
        for source in sources:
            avg_rating = source.get("avg_rating", 0)
            created = source.get("created", "")
            days_since_creation = self.calculate_days_since_creation(created)
            if days_since_creation <= self.DAYS_THRESHOLD and avg_rating >= self.AVG_RATING_THRESHOLD:
                filtered_sources.append(source)
        return filtered_sources

    def calculate_days_since_creation(self, created: str) -> int:
        created_date = datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
        days_since_creation = (datetime.now() - created_date).days
        return days_since_creation

    def collect_source_details_to_data_storage(self, sources):
        top_data_storage = DataStorage()
        for course in sources:
            course_info = self.get_course_info(course)
            course_info["content"] = self.fetch_detailed_content(course['id'])
            top_data_storage.add_data(self.platform_name, course["title"], **course_info)
        return top_data_storage

    def fetch_detailed_content(self, course_id) -> Dict[str, List[str]]:
        items = []
        page = 1
        while True:
            url = f"{self.BASE_URL}{course_id}/public-curriculum-items?page={page}"
            headers = {
                "Authorization": f"Basic {self.encoded_credentials}",
                "Accept": "application/json",
            }

            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                print(f"Failed to retrieve course content: {response.status_code}")
                break

            page_items = response.json().get('results', [])
            if not page_items:
                break

            items.extend(page_items)
            page += 1

        content = self.structure_curriculum(items)
        return content

    def structure_curriculum(self, items) -> Dict[str, List[str]]:
        content = {}
        current_chapter = None

        for item in items:
            if item['_class'] == 'chapter':
                current_chapter = item['title']
                content[current_chapter] = []
            elif item['_class'] == 'lecture':
                if current_chapter:
                    content[current_chapter].append(item['title'])
                else:
                    if 'No Chapter' not in content:
                        content['No Chapter'] = []
                    content['No Chapter'].append(item['title'])
        return content

    def get_course_info(self, course):
        return {
            "url": self.COURSE_URL_PREFIX + course["url"],
        }

if __name__ == "__main__":
    queries = ["machine learning"]
    questions = ["What is the best habit to follow every day?", "What are the prerequisites for this course?"]
    udemy_processor = UdemyProcessor()
    combined_data = udemy_processor.process(
        queries, num_sources_per_query=1, questions=questions
    )
    combined_data.save_to_yaml("udemy_courses.yaml")
    print(combined_data.to_dict())
