from src.webscrappers.jina_scrapper import JinaScrapper
from src.webscrappers.beautifulsoup_scrapper import BeautifulSoupScrapper


class ScrapperFactory:
    @staticmethod
    def create_scrapper(scrapper_type: str):
        if scrapper_type == "Jina":
            return JinaScrapper()
        elif scrapper_type == "BeautifulSoup":
            return BeautifulSoupScrapper()
        else:
            raise ValueError(f"Unknown scrapper type: {scrapper_type}")
