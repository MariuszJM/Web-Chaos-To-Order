import requests
import base64
from credentials.credentials import GITHUB_TOKEN
from datetime import datetime
from src.processors.base_processor import InDepthProcessor


class GitHubProcessor(InDepthProcessor):
    BASE_URL = "https://api.github.com/search/repositories"
    README_URL_TEMPLATE = "https://api.github.com/repos/{repo_full_name}/readme"
    STARS_THRESHOLD = 50
    DAYS_THRESHOLD = 365

    def __init__(self, platform_name="github"):
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

    def filter_low_quality_sources(self, sources, time_horizon):
        filtered_sources = []
        
        for source in sources:
            stars = source.get("stargazers_count", 0)
            updated_at = source.get("updated_at", "")
            created_at = source.get("created_at", "")
            days_since_update = self.calculate_days_passed(updated_at)
            days_since_creation = self.calculate_days_passed(created_at)
            if stars >= self.STARS_THRESHOLD and days_since_update <= self.DAYS_THRESHOLD and days_since_creation <= time_horizon:
                filtered_sources.append(source)
        
        return filtered_sources

    def calculate_days_passed(self, date):
        updated_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        days_since_update = (datetime.now() - updated_date).days
        return days_since_update

    def collect_source_details(self, sources):
        top_data_items = []
        for repo in sources:
            repo_info = self.get_repo_info(repo)
            readme_content = self.fetch_detailed_content(repo["full_name"])
            repo_info["content"] = readme_content
            repo_info['title'] = repo["full_name"]
            top_data_items.append(repo_info)
        return top_data_items

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
