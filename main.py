from github_processor import GitHubProcessor
from udemy_processor import UdemyProcessor
from youtube_processor import YouTubeProcessor
from data_storage import DataStorage


if __name__ == "__main__":
    queries = ["machine learning"]
    questions = ["What is the best habit to follow every day?", "What are the prerequisites for this course?"]

    combined_data = DataStorage()

    # Udemy
    udemy_processor = UdemyProcessor()
    udemy_combined_data = udemy_processor.process(
        queries, num_sources_per_query=num_sources_per_query, questions=questions
    )
    combined_data.combine(udemy_combined_data)

    # YouTube
    youtube_processor = YouTubeProcessor()
    youtube_combined_data = youtube_processor.process(
        queries, num_sources_per_query=num_sources_per_query, questions=questions
    )
    combined_data.combine(youtube_combined_data)

    # GitHub
    github_questions = questions + ["Does the project support Docker?"]
    github_processor = GitHubProcessor()
    github_combined_data = github_processor.process(
        queries, num_sources_per_query=num_sources_per_query, questions=github_questions
    )
    combined_data.combine(github_combined_data)

    combined_data.save_to_yaml("combined_data.yaml")
    print("Combined Data:", combined_data.to_dict())
