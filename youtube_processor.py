import os
import datetime
from typing import List
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from youtube_transcript_api import YouTubeTranscriptApi
from data_storage import DataStorage
from base_processor import SourceProcessor


class YouTubeProcessor(SourceProcessor):
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    TOKEN_PATH = "token.json"
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self, platform_name="YouTube"):
        self.platform_name = platform_name
        self.youtube = self.authenticate_youtube()

    def authenticate_youtube(self):
        creds = None
        if os.path.exists(self.TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(self.TOKEN_PATH, self.SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS_FILE, self.SCOPES)
            creds = flow.run_local_server(port=0)
            with open(self.TOKEN_PATH, "w") as token:
                token.write(creds.to_json())
        return build("youtube", "v3", credentials=creds)

    def combine_multiple_queries(self, queries: List[str], num_sources_per_query: int) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_storage = self.process_query(query, num_sources_per_query)
            combined_storage.combine(query_storage)
        return combined_storage

    def process_query(self, query: str, num_top_sources: int) -> DataStorage:
        response = self.youtube.search().list(q=query, part="snippet", maxResults=num_top_sources * 100, type="video").execute()
        scored_videos = []

        for item in response["items"]:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            title = snippet["title"]

            video_details = self.get_video_details(video_id)
            score = self.calculate_score(video_details)
            url = f"https://www.youtube.com/watch?v={video_id}"
            scored_videos.append((score, self.platform_name, title, url, video_id))

        scored_videos.sort(reverse=True, key=lambda x: x[0])
        top_videos = scored_videos[:num_top_sources]

        top_data_storage = DataStorage()
        for score, source, title, url, video_id in top_videos:
            transcript = self.get_transcript(video_id)
            top_data_storage.add_data(source, title, url=url, details=transcript)

        return top_data_storage

    def get_video_details(self, video_id):
        response = self.youtube.videos().list(part="statistics,snippet", id=video_id).execute()["items"][0]
        published_date = datetime.datetime.strptime(response["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ")
        days_since_published = (datetime.datetime.now() - published_date).days
        return {
            "view_count": int(response["statistics"].get("viewCount", 0)),
            "like_count": int(response["statistics"].get("likeCount", 0)),
            "comment_count": int(response["statistics"].get("commentCount", 0)),
            "days_since_published": days_since_published,
        }

    def calculate_score(self, video_data):
        days_since_published = max(video_data["days_since_published"], 1)
        return (
            (video_data["view_count"] * 0.4)
            + (video_data["like_count"] * 0.3)
            + (video_data["comment_count"] * 0.2)
        ) / days_since_published

    def get_transcript(self, video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry["text"] for entry in transcript])
        except Exception:
            transcript_text = "Transcript not available."
        return transcript_text


if __name__ == "__main__":
    queries = ["Python tutorial", "Python"]
    youtube_processor = YouTubeProcessor()
    combined_data = youtube_processor.combine_multiple_queries(queries, num_sources_per_query=5)
    combined_data.save_to_yaml("youtube_data.yaml")
    print(combined_data.to_dict())
