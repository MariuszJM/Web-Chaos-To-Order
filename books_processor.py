import requests
from typing import List
from data_storage import DataStorage
from base_processor import SourceProcessor


class GoogleBooksProcessor(SourceProcessor):
    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def __init__(self):
        self.platform_name = "Google Books"

    def combine_multiple_queries(
        self, queries: List[str], num_sources_per_query: int
    ) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_storage = self.process_query(query, num_sources_per_query)
            combined_storage.combine(query_storage)
        return combined_storage

    def process_query(self, query: str, num_sources: int) -> DataStorage:
        response = self.search(query, num_sources)

        books = response["items"]
        data_storage = DataStorage()

        for book in books:
            book_info = self.get_book_info(book)
            data_storage.add_data(self.platform_name, **book_info)

        return data_storage

    def search(self, query: str, max_results):
        params = {
            "q": query,
            "maxResults": max_results,
            "orderBy": "relevance",
        }
        response = requests.get(self.BASE_URL, params=params)

        if response.status_code != 200:
            print(f"Failed to retrieve books: {response.status_code}")
            return None
        return response.json()

    def get_book_info(self, book):
        volume_info = book.get("volumeInfo", {})
        return {
            "title": volume_info.get("title", "No title"),
            "published_date": volume_info.get("publishedDate", "No date"),
            "description": volume_info.get("description", ""),
            "url": volume_info.get("previewLink", ""),
            "language": volume_info.get("language", "unknown"),
        }


if __name__ == "__main__":
    queries = ["machine learning", "data science"]
    google_books_processor = GoogleBooksProcessor()
    combined_data = google_books_processor.combine_multiple_queries(queries, num_sources_per_query=5)
    combined_data.save_to_yaml("google_books_data.yaml")
    print(combined_data.to_dict())
