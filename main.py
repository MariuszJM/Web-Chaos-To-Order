import os
import yaml
from src.processors.github_processor import GitHubProcessor
from src.processors.udemy_processor import UdemyProcessor
from src.processors.youtube_processor import YouTubeProcessor
from src.data_storage import DataStorage
from src.llm import LLM
from src.utils import load_config, create_output_directory


if __name__ == "__main__":
    execution_config = load_config('./config/execution_config.yaml')
    sources_per_query = execution_config['sources_per_query']
    user_config = load_config('./config/user_config.yaml')
    queries = user_config['search_phrases']
    platforms = [platform.lower() for platform in user_config['platforms']]
    max_outputs_per_platform = user_config['max_outputs_per_platform']
    specific_questions = user_config['specific_questions']

    llm = LLM()
    name = llm.provide_run_name(queries, specific_questions)
    combined_data = DataStorage()
    data_witout_content = DataStorage()
    rejected_data = DataStorage()
    if 'youtube' in platforms:
        platforms.remove('youtube')
        youtube_processor = YouTubeProcessor()
        yt_top_data, yt_data_witout_content, yt_rejected_data = youtube_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(yt_top_data)
        data_witout_content.combine(yt_data_witout_content)
        rejected_data.combine(yt_rejected_data)

    if 'github' in platforms:
        platforms.remove('github')
        github_processor = GitHubProcessor()
        git_top_data, git_data_witout_content, git_rejected_data = github_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(git_top_data)
        data_witout_content.combine(git_data_witout_content)
        rejected_data.combine(git_rejected_data)
    
    if 'udemy' in platforms:
        platforms.remove('udemy')
        udemy_processor = UdemyProcessor()
        u_top_data, u_data_witout_content, u_rejected_data = udemy_processor.process(
            queries, sources_per_query=sources_per_query, questions=specific_questions
        )
        combined_data.combine(u_top_data)
        data_witout_content.combine(u_data_witout_content)
        rejected_data.combine(u_rejected_data)

    if len(platforms) != 0: 
        print(f"Platrofms: {platforms} are not available")

    output_dir = create_output_directory('runs')
    combined_data.save_to_yaml(os.path.join(output_dir, f"{name}.yaml"))
    data_witout_content.save_to_yaml(os.path.join(output_dir, f"data_witout_content.yaml"))
    rejected_data.save_to_yaml(os.path.join(output_dir, f"rejected_data.yaml"))
    
    with open(os.path.join(output_dir, f"run_config.yaml"), "w") as file:
            yaml.dump(user_config, file, default_flow_style=False, sort_keys=False)
    print("Combined Data:", combined_data.to_dict())
    print(f"Data saved to: {output_dir}")
