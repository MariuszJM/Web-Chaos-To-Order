from src.utils import create_output_directory, load_config, save_data
from src.processors.platforms_processor import process_platforms

def main():
    config = load_config('./config/config.yaml')
    sources_per_query = config['sources_per_query']
    search_phrases = config['search_phrases']
    platforms = [platform.lower() for platform in config['platforms']]
    max_outputs = config['max_outputs_per_platform']
    time_horizon = config['time_horizon']
    specific_questions = config['specific_questions']

    results, rest_results, run_name = process_platforms(
        platforms, search_phrases, sources_per_query, specific_questions, time_horizon, max_outputs
    )

    output_dir = create_output_directory('runs')
    save_data(output_dir, run_name, results, rest_results, config)

    print("Combined Results:", results.to_dict())
    print(f"Data saved to: {output_dir}")

if __name__ == "__main__":
    main()
