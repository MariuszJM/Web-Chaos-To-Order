from googleapiclient.discovery import build
from credentials.credentials import GOOGLE_CSE_ID, GOOGLE_KEY
from src.processors.base_processor import BaseProcessor
from src.webscrappers.scrapper_factory import ScrapperFactory


SCRAPPER_TYPE = 'Jina'


class GoogleProcessor(BaseProcessor):
    QUALITY_THRESHOLD = 0.2

    def __init__(self, platform_name="google"):
        super().__init__(platform_name)
        self.google = self.authenticate_google()
        self.scrapper = ScrapperFactory.create_scrapper(scrapper_type=SCRAPPER_TYPE)
    def authenticate_google(self):
        return build("customsearch", "v1", developerKey=GOOGLE_KEY)

    def process_query(self, query: str, time_horizon):
        response = self.google.cse().list(q=query, cx=GOOGLE_CSE_ID, num=self.SOURCES_PER_QUERY, dateRestrict=f"d{time_horizon}").execute()
        sources = response.get("items", [])
        data = []
        for item in sources:
            link = item.get("link")
            item_details = {'title': item.get("title"), 
                            'url':link, 
                            'content':self.fetch_detailed_content(link)}
            data.append(item_details)
        return data
        
    def fetch_detailed_content(self, url):
        webside_content = self.scrapper.fetch_website_content(url)
        return webside_content