import logging
from src.utils import create_output_directory, load_config, save_data
from src.processors.platforms_processor import process_platforms

output_dir = create_output_directory('runs')

log_filename = f"{output_dir}/app.log"
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)  

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


def main():
    config = load_config('./config/config.yaml')
    logger.debug("Configuration loaded.")
    sources_per_query = config['sources_per_query']
    search_phrases = config['search_phrases']
    platforms = [platform.lower() for platform in config['platforms']]
    max_outputs = config['max_outputs_per_platform']
    time_horizon = config['time_horizon']
    specific_questions = config['specific_questions']

    results, rest_results, run_name = process_platforms(
        platforms, search_phrases, sources_per_query, specific_questions, time_horizon, max_outputs
    )

    save_data(output_dir, run_name, results, rest_results, config)

    logger.info("Data saved to: %s", output_dir)

if __name__ == "__main__":
    main()
