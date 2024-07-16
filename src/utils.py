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