import base64
from github_processor import GitHubProcessor
from udemy_processor import UdemyProcessor
from youtube_processor import YouTubeProcessor
from data_storage import DataStorage
from config import UDEMY_SECRET_KEY, UDEMY_CLIENT_ID


if __name__ == "__main__":
    queries = ["machine learning"]
    questions = ["What is the best habit to follow every day?", "What are the prerequisites for this course?"]

    combined_data = DataStorage()

    # Udemy
    credentials = f"{UDEMY_CLIENT_ID}:{UDEMY_SECRET_KEY}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    udemy_processor = UdemyProcessor(encoded_credentials)
    udemy_combined_data = udemy_processor.combine_multiple_queries(
        queries, num_sources_per_query=1, questions=questions
    )
    combined_data.combine(udemy_combined_data)

    # YouTube
    youtube_processor = YouTubeProcessor()
    youtube_combined_data = youtube_processor.combine_multiple_queries(
        queries, num_sources_per_query=1, questions=questions
    )
    combined_data.combine(youtube_combined_data)

    # GitHub
    github_questions = questions + ["Does the project support Docker?"]
    github_processor = GitHubProcessor()
    github_combined_data = github_processor.combine_multiple_queries(
        queries, num_sources_per_query=5, questions=github_questions
    )
    combined_data.combine(github_combined_data)

    combined_data.save_to_yaml("combined_data.yaml")
    print("Combined Data:", combined_data.to_dict())
