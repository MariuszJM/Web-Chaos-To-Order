from googleapiclient.discovery import build
from credentials.credentials import GOOGLE_CSE_ID, GOOGLE_KEY
from src.processors.base_processor import BaseProcessor
from src.webscrappers.scrapper_factory import ScrapperFactory
import multiprocessing


SCRAPPER_TYPE = 'BeautifulSoup'



def fetch_with_timeout_multiprocessing(fetch_function, url, timeout):
    def target(queue):
        try:
            result = fetch_function(url)
            queue.put(result)
        except Exception as e:
            queue.put(e)

    queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=target, args=(queue,))
    process.start()
    process.join(timeout)

    if process.is_alive():
        process.terminate()  # Zabij proces, jeśli nadal działa po timeout
        process.join()
        print(f"Fetching content from {url} timed out after {timeout} seconds.")
        return None
    else:
        result = queue.get()
        if isinstance(result, Exception):
            raise result
        return result

class GoogleProcessor(BaseProcessor):
    QUALITY_THRESHOLD = 0.2

    def __init__(self, platform_name="google"):
        super().__init__(platform_name)
        self.google = self.authenticate_google()
        self.scrapper_bs = ScrapperFactory.create_scrapper(scrapper_type='BeautifulSoup')
        self.scrapper_jina = ScrapperFactory.create_scrapper(scrapper_type='Jina')
        self.country_code = "PL"
    def authenticate_google(self):
        return build("customsearch", "v1", developerKey=GOOGLE_KEY)

    def process_query(self, query: str, time_horizon):
        response = self.google.cse().list(q=query, cx=GOOGLE_CSE_ID, num=self.SOURCES_PER_QUERY, gl=self.country_code, dateRestrict=f"d{time_horizon}").execute()
        sources = response.get("items", [])
        data = []
        for item in sources:
            link = item.get("link")
            item_details = {'title': item.get("title"), 
                            'url':link, 
                            'content':self.fetch_detailed_content(link)}
            data.append(item_details)
        return data
        
    def fetch_detailed_content(self, url, timeout=10):
        try:
            # Spróbuj pobrać treść za pomocą scrapper_bs z limitem czasu
            webside_content = fetch_with_timeout_multiprocessing(self.scrapper_bs.fetch_website_content, url, timeout)
            if webside_content is not None:
                return webside_content
            else:
                raise TimeoutError("Timeout reached for scrapper_bs.")
        except Exception as e_bs:
            print(f"Error fetching content from {url} using scrapper_bs: {str(e_bs)}")
            try:
                # Spróbuj pobrać treść za pomocą strapper_jina z limitem czasu
                webside_content = fetch_with_timeout_multiprocessing(self.scrapper_jina.fetch_website_content, url, timeout)
                if webside_content is not None:
                    return webside_content
                else:
                    raise TimeoutError("Timeout reached for strapper_jina.")
            except Exception as e_jina:
                print(f"Error fetching content from {url} using strapper_jina: {str(e_jina)}")
                return None
