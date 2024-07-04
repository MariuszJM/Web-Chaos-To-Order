import os
import datetime
from typing import List
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from youtube_transcript_api import YouTubeTranscriptApi
from data_storage import DataStorage
from base_processor import SourceProcessor
import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
        combined_storage = self.add_summary_info(combined_storage)
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

    def split_text_to_chunks(self, text, chunk_size=7500, chunk_overlap=150):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(text)

    def summarize_transcript(self, transcript, chunk_size=7500):
        if not transcript:
            return "Transcript not available."
        chunks = self.split_text_to_chunks(transcript, chunk_size=chunk_size)
        questions = 'What is the best habit to follow every day?'
        Summary_format = """**Overview**


      overwiew content...


      **first summary point name**


      First summary point content...
      
      **second summary point name**


      Second summary point content...
      
      etc...

"""
        summaries = []
        for chunk in chunks:
            prompt = (f"""You are an expert content summarizer. Summarize the video based on the following transcript. 
                      Focus on essential information and answer the following questions: {questions}
                      Use bullet points and separate each point with a newline and the following output format: {Summary_format}.
                      Transcript: {chunk}""")
            response = ollama.generate(model="llama3:instruct", prompt=prompt)
            summary = response.get('response', "").strip()
            summaries.append(summary)
        
        combine_flag = False
        if len(summaries) > 1:
            combine_flag = True

        combined_summary = "\n".join(summaries)
        if len(self.tokenize(combined_summary)) > 7500:
            combined_summary, _ = self.summarize_transcript(combined_summary, chunk_size=7500)
        
        return combined_summary, combine_flag

    def tokenize(self, text):
        return text.split()

    def add_summary_info(self, data_storage: DataStorage) -> DataStorage:
        for source in data_storage.data.keys():
            for title in data_storage.data[source].keys():
                transcript = data_storage.data[source][title]["details"]
                summary, combine_flag = self.summarize_transcript(transcript)
                if combine_flag:
                    combined_summary = self.organize_summarization_into_one(summary)    
                data_storage.data[source][title]["detailed_summary"] = summary
                data_storage.data[source][title]["summary"] = combined_summary

                # Process list of questions
                questions = ['What is the best habit to follow every day?', "What Can I do to protect my skin?", "What seems to be the best habit to protect my skin?"]
                for question in questions:
                    is_relevant = self.ask_llama_relevance(question, transcript, summary)
                    if "yes" in is_relevant.lower():
                        answer = self.ask_llama_question(question, transcript, summary)
                        if "questions" not in data_storage.data[source][title]:
                            data_storage.data[source][title]["questions"] = {}
                        data_storage.data[source][title]["questions"][question] = answer
        
        return data_storage

    def organize_summarization_into_one(self, combined_text: str) -> str:
        prompt = (f"""You are an expert content information organizer. Combine and organize the following summaries into a single cohesive summary. 
                    Remove redundant informations.
                    Make it  as detaild as possible. The output shouldn't be much smaller that the input. You are not summarizer just organizer.
                    Use bullet points and the following output format:
                    
                    **Overview**

                    Overview content...

                    **Summary Points**

                    - First summary point content...
                    - Second summary point content...
                    - etc...

                    Summaries: {combined_text}""")

        response = ollama.generate(model="llama3:instruct", prompt=prompt)
        organized_summary = response.get('response', "").strip()
        return organized_summary

    def ask_llama_relevance(self, question: str, details: str, detailed_summary: str) -> str:
        text = details if len(self.tokenize(details)) <= 7500 else detailed_summary
        prompt = f"""
        Is the text below at least partially relevant to my question? Say Yes or No.

        question:
        {question}

        text:
        {text}
        """
        response = ollama.generate(model="llama3:instruct", prompt=prompt)
        answer = response.get('response', "").strip()
        return answer

    def ask_llama_question(self, question: str, details: str, detailed_summary: str) -> str:
        text = details if len(self.tokenize(details)) <= 7500 else detailed_summary
        prompt = f"""
        Based on the text, answer the question: {question}
        
        text:
        {text}
        """
        response = ollama.generate(model="llama3:instruct", prompt=prompt)
        answer = response.get('response', "").strip()
        return answer

if __name__ == "__main__":
    queries = ["Huberman podcast"]
    youtube_processor = YouTubeProcessor()
    combined_data = youtube_processor.combine_multiple_queries(queries, num_sources_per_query=1)
    combined_data.save_to_yaml("youtube_data.yaml")
    print(combined_data.to_dict())
