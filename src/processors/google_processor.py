from googleapiclient.discovery import build
from src.data_storage import DataStorage
from src.processors.base_processor import SourceProcessor
from credentials.credentials import GOOGLE_CSE_IDS, GOOGLE_KEY
import requests


class GoogleProcessor(SourceProcessor):
    QUALITY_THRESHOLD = 0.2

    def __init__(self, platform_name="Google"):
        super().__init__(platform_name)
        self.google = self.authenticate_google()
    def authenticate_google(self):
        return build("customsearch", "v1", developerKey=GOOGLE_KEY)

    def fetch_source_items(self, query, limit):
        # Ensure limit does not exceed 10
        if limit > 10:
            limit = 10
        response = self.google.cse().list(q=query, cx=GOOGLE_CSE_IDS[self.platform_name], num=limit, dateRestrict="d199").execute()
        return response.get("items", [])

    def filter_low_quality_sources(self, sources, time_horizon):
        # Placeholder implementation
        # To be implemented with appropriate quality assessment logic
        return sources

    def collect_source_details_to_data_storage(self, sources):
        top_data_storage = DataStorage()
        for item in sources:
            title = item.get("title")
            link = item.get("link")
            snippet = f'Short Description {item.get("snippet")} /n {self.fetch_detailed_content(link)}'
            top_data_storage.add_data(self.platform_name, title, url=link, content=snippet)

        return top_data_storage

    def fetch_detailed_content(self, url):
        response = requests.get("https://r.jina.ai/"+ url)
        return response.text