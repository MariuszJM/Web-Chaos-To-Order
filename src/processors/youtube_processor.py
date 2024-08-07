import os
from datetime import datetime
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from youtube_transcript_api import YouTubeTranscriptApi
from google.auth.transport.requests import Request
from src.processors.base_processor import InDepthProcessor


class YouTubeProcessor(InDepthProcessor):
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    TOKEN_PATH = "./credentials/token.json"
    CREDENTIALS_FILE = "./credentials/credentials.json"
    QUALITY_THRESHOLD = 0.2

    def __init__(self, platform_name="youtube"):
        super().__init__(platform_name)
        self.youtube = self.authenticate_youtube()

    def authenticate_youtube(self):
        creds = None
        if os.path.exists(self.TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(self.TOKEN_PATH, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.CREDENTIALS_FILE, self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open(self.TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        return build("youtube", "v3", credentials=creds)

    def fetch_source_items(self, query, limit):
        response = self.youtube.search().list(q=query, part="snippet", maxResults=limit, type="video").execute()
        return response["items"]

    def filter_low_quality_sources(self, sources, time_horizon):
        filtered_sources = []
        for item in sources:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            title = snippet["title"]
            published_at = snippet["publishedAt"]
            days_since_creation = self.calculate_days_passed(published_at)
            video_details = self.get_video_details(video_id)
            quality = self.calculate_quality(video_details)
            if quality > self.QUALITY_THRESHOLD and days_since_creation <= time_horizon:
                url = f"https://www.youtube.com/watch?v={video_id}"
                filtered_sources.append((self.platform_name, title, url, video_id))
        return filtered_sources

    def calculate_days_passed(self, date: str) -> int:
        created_date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%SZ")
        days_since_creation = (datetime.now() - created_date).days
        return days_since_creation
    
    def collect_source_details(self, sources):
        data = []
        for _, title, url, video_id in sources:
            item_details = {'title': title, 
                            'url':url, 
                            'content':self.fetch_detailed_content(video_id)}
            data.append(item_details)
        return data

    def get_video_details(self, video_id):
        response = self.youtube.videos().list(part="statistics,snippet", id=video_id).execute()["items"][0]
        channel_id = response["snippet"]["channelId"]
        channel_response = self.youtube.channels().list(part="statistics", id=channel_id).execute()["items"][0]
        subscriber_count = int(channel_response["statistics"].get("subscriberCount", 0))

        return {
            "view_count": int(response["statistics"].get("viewCount", 0)),
            "like_count": int(response["statistics"].get("likeCount", 0)),
            "comment_count": int(response["statistics"].get("commentCount", 0)),
            "subscriber_count": subscriber_count,
        }

    def calculate_quality(self, video_data):
        view_count = video_data["view_count"]
        subscriber_count = video_data["subscriber_count"]
        like_count = video_data["like_count"]
        comment_count = video_data["comment_count"]

        if subscriber_count == 0:
            subscriber_ratio = 0
        else:
            subscriber_ratio = view_count / subscriber_count

        if view_count == 0:
            like_ratio = 0
            comment_ratio = 0
        else:
            like_ratio = like_count / view_count
            comment_ratio = comment_count / view_count

        quality = (
            (subscriber_ratio * 0.4)
            + (like_ratio * 0.4)
            + (comment_ratio * 0.2)
        )
        return quality

    def fetch_detailed_content(self, video_id):
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry["text"] for entry in transcript])
        except Exception:
            transcript_text = "Transcript not available."
        return transcript_text

