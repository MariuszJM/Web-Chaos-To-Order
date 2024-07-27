import requests
from src.webscrappers.base_scrapper import BaseScrapper

class JinaScrapper(BaseScrapper):
    def fetch_website_content(self, url):
        response = requests.get("https://r.jina.ai/" + url)
        return response.text