import base64
import requests
from typing import List, Dict
from data_storage import DataStorage
from base_processor import SourceProcessor
from config import UDEMY_SECRET_KEY, UDEMY_CLIENT_ID
from LLMProcessor import LLMProcessor

class UdemyProcessor(SourceProcessor):
    BASE_URL = "https://www.udemy.com/api-2.0/courses/"
    COURSE_URL_PREFIX = "https://www.udemy.com"

    def __init__(self, encoded_credentials, platform_name="Udemy"):
        self.platform_name = platform_name
        self.encoded_credentials = encoded_credentials
        self.llm_processor = LLMProcessor()

    def combine_multiple_queries(self, queries: List[str], num_sources_per_query: int) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_storage = self.process_query(query, num_sources_per_query)
            combined_storage.combine(query_storage)
        combined_storage = self.add_summary_info(combined_storage)
        return combined_storage

    def process_query(self, query: str, num_top_sources: int) -> DataStorage:
        response = self.search(query, num_top_sources)
        if response is None:
            return DataStorage()

        courses = response["results"][:num_top_sources]

        top_data_storage = DataStorage()
        for course in courses:
            course_info = self.get_course_info(course)
            course_info['details'] = self.get_course_content(course['id'])
            top_data_storage.add_data(self.platform_name, course["title"], **course_info)

        return top_data_storage

    def search(self, query: str, max_results):
        params = {
            "search": query,
            "page_size": max_results,
            "ordering": "relevance",
        }
        headers = {
            "Authorization": f"Basic {self.encoded_credentials}",
            "Accept": "application/json",
        }

        response = requests.get(self.BASE_URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve courses: {response.status_code}")
            return None
        return response.json()

    def get_course_info(self, course):
        return {
            "url": self.COURSE_URL_PREFIX + course["url"],
        }

    def get_course_content(self, course_id) -> Dict[str, List[str]]:
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

        print(f"Curriculum items for course {course_id}: {items}")  # Debugging output
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

        print(f"Structured curriculum: {content}")  # Debugging output
        return content

    def add_summary_info(self, data_storage: DataStorage) -> DataStorage:
        for course_title in data_storage.data[self.platform_name].keys():
            details = data_storage.data[self.platform_name][course_title]["details"]
            details_str = "\n".join(
                [f"{chapter}: {', '.join(lectures)}" for chapter, lectures in details.items()]
            )
            
            if len(self.llm_processor.tokenize(details_str)) > 7500:
                detailed_summary, _ = self.llm_processor.summarize_transcript(details_str)
                data_storage.data[self.platform_name][course_title]["detailed_summary"] = detailed_summary
                combined_summary = self.llm_processor.organize_summarization_into_one(detailed_summary)
                data_storage.data[self.platform_name][course_title]["summary"] = combined_summary
                summary_source = detailed_summary
            else:
                summary = self.llm_processor.summarize_readme(details_str)
                data_storage.data[self.platform_name][course_title]["summary"] = summary
                summary_source = details_str

            # Process list of questions
            questions = ["What is the best habit to follow every day?"]
            for question in questions:
                answer = self.llm_processor.ask_llama_question(question, details_str, summary_source)
                if "Q&A" not in data_storage.data[self.platform_name][course_title]:
                    data_storage.data[self.platform_name][course_title]["Q&A"] = {}
                data_storage.data[self.platform_name][course_title]["Q&A"][question] = answer

        return data_storage

if __name__ == "__main__":
    credentials = f"{UDEMY_CLIENT_ID}:{UDEMY_SECRET_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

    queries = ["machine learning"]
    udemy_processor = UdemyProcessor(encoded_credentials)
    combined_data = udemy_processor.combine_multiple_queries(
        queries, num_sources_per_query=1
    )
    combined_data.save_to_yaml("udemy_courses.yaml")
    print(combined_data.to_dict())
