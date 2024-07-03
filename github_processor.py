import requests
from typing import List
from data_storage import DataStorage
from base_processor import SourceProcessor


class GitHubProcessor(SourceProcessor):
    BASE_URL = "https://api.github.com/search/repositories"

    def __init__(self, platform_name="GitHub"):
        self.platform_name = platform_name

    def combine_multiple_queries(
        self, queries: List[str], num_sources_per_query: int
    ) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_storage = self.process_query(query, num_sources_per_query)
            combined_storage.combine(query_storage)
        return combined_storage

    def process_query(self, query: str, num_top_sources: int) -> DataStorage:
        response = self.search(query, num_top_sources)
        if response is None:
            return DataStorage()

        repositories = response["items"][:num_top_sources]

        top_data_storage = DataStorage()
        for repo in repositories:
            repo_info = self.get_repo_info(repo)
            top_data_storage.add_data(self.platform_name, repo["full_name"], **repo_info)

        return top_data_storage

    def search(self, query: str, max_results):
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }
        headers = {"Accept": "application/vnd.github.v3+json"}

        response = requests.get(self.BASE_URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve repositories: {response.status_code}")
            return None
        return response.json()

    def get_repo_info(self, repo):
        return {
            "url": repo["html_url"],
            "description": repo["description"],
            "language": repo["language"],
        }


if __name__ == "__main__":
    queries = ["machine learning", "data science"]
    github_processor = GitHubProcessor()
    combined_data = github_processor.combine_multiple_queries(queries, num_sources_per_query=5)
    combined_data.save_to_yaml("github_repositories.yaml")
    print(combined_data.to_dict())
