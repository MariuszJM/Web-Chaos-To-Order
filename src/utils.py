import yaml
import os
import datetime


def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)
    
def create_output_directory(base_dir):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_dir = os.path.join(base_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def save_data(output_dir, name, results_data, rest_data, user_config):
    results_data.save_to_yaml(os.path.join(output_dir, f"{name}.yaml"))
    with open(os.path.join(output_dir, f"filtered_data.yaml"), "w") as file:
        yaml.dump(rest_data, file, default_flow_style=False, sort_keys=False)
    with open(os.path.join(output_dir, f"run_config.yaml"), "w") as file:
        yaml.dump(user_config, file, default_flow_style=False, sort_keys=False)