from src.processors.github_processor import GitHubProcessor
from src.processors.udemy_processor import UdemyProcessor
from src.processors.youtube_processor import YouTubeProcessor
from src.data_storage import DataStorage
from src.utils import load_config


if __name__ == "__main__":
    config = load_config('./config/config.yaml')

    queries = config['search_phrases']
    platforms = [platform.lower() for platform in config['platforms']]
    sources_per_query = config['sources_per_query']
    max_outputs_per_platform = config['max_outputs_per_platform']
    specific_questions = config['specific_questions']

    combined_data = DataStorage()

    if 'udemy' in platforms:
        platforms.remove('udemy')
        udemy_processor = UdemyProcessor()
        udemy_combined_data = udemy_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(udemy_combined_data)

    if 'youtube' in platforms:
        platforms.remove('youtube')
        youtube_processor = YouTubeProcessor()
        youtube_combined_data = youtube_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(youtube_combined_data)

    if 'github' in platforms:
        platforms.remove('github')
        github_processor = GitHubProcessor()
        github_combined_data = github_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(github_combined_data)
    
    if len(platforms) != 0: 
        print(f"Platrofms: {platforms} are not available")

    combined_data.save_to_yaml("combined_data.yaml")
    print("Combined Data:", combined_data.to_dict())
