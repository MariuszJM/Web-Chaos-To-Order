from googleapiclient.discovery import build
from src.data_storage import DataStorage
from src.processors.base_processor import BaseProcessor
from credentials.credentials import GOOGLE_CSE_IDS, GOOGLE_KEY
import requests


class GoogleProcessor(BaseProcessor):
    QUALITY_THRESHOLD = 0.2

    def __init__(self, platform_name="Google"):
        super().__init__(platform_name)
        self.google = self.authenticate_google()
    def authenticate_google(self):
        return build("customsearch", "v1", developerKey=GOOGLE_KEY)

    def process_query(self, query: str, num_top_sources: int, time_horizon) -> DataStorage:
        if num_top_sources > 10:
            num_top_sources = 10
        response = self.google.cse().list(q=query, cx=GOOGLE_CSE_IDS[self.platform_name], num=num_top_sources, dateRestrict=f"d{time_horizon}").execute()
        sources = response.get("items", [])
        data_storage = DataStorage()
        for item in sources:
            title = item.get("title")
            link = item.get("link")
            snippet = f'Short Description {item.get("snippet")} /n {self.fetch_detailed_content(link)}'
            data_storage.add_data(self.platform_name, title, url=link, content=snippet)
        return data_storage
        
    def fetch_detailed_content(self, url):
        response = requests.get("https://r.jina.ai/"+ url)
        return response.text