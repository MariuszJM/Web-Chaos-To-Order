import logging
import os
import glob
from src.utils import create_output_directory, load_config, save_data
from src.processors.process_platforms import process_platforms

def setup_logging(output_dir):
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

    return logger

def process_config_file(config_file, logger):
    config = load_config(config_file)
    logger.info(f"Configuration loaded from {config_file}.")
    output_dir = create_output_directory(config['output_dir'])
    setup_logging(output_dir)
    
    search_phrases = config['search_queries']
    platforms = [platform.lower() for platform in config['platforms']]
    max_outputs = config['max_outputs_per_platform']
    time_horizon = config['time_horizon']
    specific_questions = config['specific_questions']

    results, rest_results = process_platforms(
        platforms, search_phrases, specific_questions, time_horizon, max_outputs
    )
    run_name = config_file.split('.')[0]
    save_data(output_dir, run_name, results, rest_results, config)

    logger.info("Data saved to: %s", output_dir)

def main(config_path):
    logger = logging.getLogger('main_logger')
    
    if os.path.isdir(config_path):
        config_files = glob.glob(os.path.join(config_path, '*.yaml'))
        for config_file in config_files:
            process_config_file(config_file, logger)
    elif os.path.isfile(config_path):
        process_config_file(config_path, logger)
    else:
        logger.error(f"Invalid path provided: {config_path}")

if __name__ == "__main__":
    config_path = './config/Jobs_Search/artificial_intelligence_machine_learning.yaml'  
    main(config_path)
