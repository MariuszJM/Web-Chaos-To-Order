import requests
from bs4 import BeautifulSoup
from src.webscrappers.base_scrapper import BaseScrapper


class BeautifulSoupScrapper(BaseScrapper):
    def fetch_website_content(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup.get_text()