import requests
import base64
from data_storage import DataStorage
from base_processor import SourceProcessor
from config import GITHUB_TOKEN

class GitHubProcessor(SourceProcessor):
    BASE_URL = "https://api.github.com/search/repositories"
    README_URL_TEMPLATE = "https://api.github.com/repos/{repo_full_name}/readme"

    def __init__(self, platform_name="GitHub"):
        super().__init__(platform_name)

    def fetch_source_items(self, query, limit):
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
        }
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {GITHUB_TOKEN}"
        }

        response = requests.get(self.BASE_URL, params=params, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve repositories: {response.status_code}")
            return []

        return response.json().get("items", [])

    def filter_low_quality_sources(self, sources):
        # Example filter: only include repositories with more than 50 stars
        return [source for source in sources if source.get("stargazers_count", 0) > 50]

    def select_top_sources(self, sources, num_top_sources):
        top_sources = sources[:num_top_sources]
        top_data_storage = DataStorage()
        
        for repo in top_sources:
            repo_info = self.get_repo_info(repo)
            readme_content = self.fetch_content(repo["full_name"])
            repo_info["details"] = readme_content
            top_data_storage.add_data(self.platform_name, repo["full_name"], **repo_info)

        return top_data_storage

    def fetch_detailed_content(self, repo_full_name: str) -> str:
        url = self.README_URL_TEMPLATE.format(repo_full_name=repo_full_name)
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            readme_info = response.json()
            readme_base64 = readme_info['content']
            readme_content = base64.b64decode(readme_base64).decode('utf-8')
            return readme_content
        else:
            print(f"Failed to fetch README for {repo_full_name}. Status code: {response.status_code}")
            return ""

    def get_repo_info(self, repo):
        return {
            "url": repo["html_url"],
            "description": repo["description"],
            "language": repo["language"],
        }

if __name__ == "__main__":
    queries = ["Open Web UI"]
    questions = ["Does the project support Docker?", "Is there a contribution guide?"]
    github_processor = GitHubProcessor()
    combined_data = github_processor.combine_multiple_queries(queries, num_sources_per_query=5, questions=questions)
    combined_data.save_to_yaml("github_repositories.yaml")
    print(combined_data.to_dict())
