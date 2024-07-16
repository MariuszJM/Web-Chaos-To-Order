import os
from src.processors.github_processor import GitHubProcessor
from src.processors.udemy_processor import UdemyProcessor
from src.processors.youtube_processor import YouTubeProcessor
from src.data_storage import DataStorage
from src.llm import LLM
from src.utils import load_config, create_output_directory


if __name__ == "__main__":
    execution_config = load_config('./config/execution_config.yaml')
    sources_per_query = execution_config['sources_per_query']
    platform_shortcuts = execution_config['platform_shortcuts']
    user_config = load_config('./config/user_config.yaml')
    queries = user_config['search_phrases']
    platforms = [platform.lower() for platform in user_config['platforms']]
    max_outputs_per_platform = user_config['max_outputs_per_platform']
    specific_questions = user_config['specific_questions']

    llm = LLM()
    name = llm.provide_run_name(queries, specific_questions)
    for platform in platforms:
        name += "_" + platform_shortcuts[platform]

    combined_data = DataStorage()

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
    
    if 'udemy' in platforms:
        platforms.remove('udemy')
        udemy_processor = UdemyProcessor()
        udemy_combined_data = udemy_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(udemy_combined_data)

    if len(platforms) != 0: 
        print(f"Platrofms: {platforms} are not available")

    output_dir = create_output_directory('runs')
    combined_data.save_to_yaml(os.path.join(output_dir, f"{name}.yaml"))
    print("Combined Data:", combined_data.to_dict())
    print(f"Data saved to: {output_dir}")
