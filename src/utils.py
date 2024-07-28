import yaml
import os
import datetime
import logging

logger = logging.getLogger(__name__)

def load_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        logger.info("Configuration loaded from file: %s", file_path)
        return config

def create_output_directory(base_dir):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(base_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    logger.debug("Output directory created: %s", output_dir)
    return output_dir

def save_data(output_dir, name, results_data, rest_data, user_config):
    results_data.save_to_yaml(os.path.join(output_dir, f"{name}.yaml"))
    with open(os.path.join(output_dir, f"rest_of_the_data.yaml"), "w") as file:
        yaml.dump(rest_data, file, default_flow_style=False, sort_keys=False)
    with open(os.path.join(output_dir, f"run_config.yaml"), "w") as file:
        yaml.dump(user_config, file, default_flow_style=False, sort_keys=False)
    logger.debug("Data saved to directory: %s", output_dir)