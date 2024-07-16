import os
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from youtube_transcript_api import YouTubeTranscriptApi
from src.data_storage import DataStorage
from src.processors.base_processor import SourceProcessor
from google.auth.transport.requests import Request

class YouTubeProcessor(SourceProcessor):
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
    TOKEN_PATH = "../token.json"
    CREDENTIALS_FILE = "credentials.json"
    QUALITY_THRESHOLD = 0.2

    def __init__(self, platform_name="YouTube"):
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

    def filter_low_quality_sources(self, sources):
        filtered_sources = []
        for item in sources:
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            title = snippet["title"]

            video_details = self.get_video_details(video_id)
            quality = self.calculate_quality(video_details)
            if quality > self.QUALITY_THRESHOLD:
                url = f"https://www.youtube.com/watch?v={video_id}"
                filtered_sources.append((self.platform_name, title, url, video_id))
        return filtered_sources

    def collect_source_details_to_data_storage(self, sources):
        top_data_storage = DataStorage()
        for source, title, url, video_id in sources:
            transcript = self.fetch_detailed_content(video_id)
            top_data_storage.add_data(source, title, url=url, content=transcript)

        return top_data_storage

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

if __name__ == "__main__":
    queries = ["LLM output fomrat problems in python", 'constrain llm output format', 'How to solve problem of unstable output format from llm?']
    questions = ['How to solve problem of unstable output format from llm?', "How to constrain the llm ouput format?", "How to solve the llm ouput format problem?"]
    youtube_processor = YouTubeProcessor()
    combined_data = youtube_processor.process(queries, num_sources_per_query=9, questions=questions)
    combined_data.save_to_yaml("youtube_data.yaml")
    print(combined_data.to_dict())
