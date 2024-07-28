import yaml
import re
import logging

logger = logging.getLogger(__name__)

class DataStorage:
    def __init__(self):
        self.data = {}

    def add_data(self, platform_name, title, **tags):
        self.data.setdefault(platform_name, {})[title] = tags
        logger.debug("Data added for platform: %s, title: %s", platform_name, title)
    
    def combine(self, data_storage):
        for platform_name, titles in data_storage.data.items():
            self.data.setdefault(platform_name, {}).update(titles)

    def add_data_list(self, platform_name, data_list):
        for item_details in data_list:
            title = item_details.pop('title')
            self.add_data(platform_name, title, **item_details)
        logger.debug("Data list added for platform: %s", platform_name)

    def to_dict(self):
        return self.data

    def clean_title(self, title):
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        return clean_title

    def save_to_yaml(self, filename):
        cleaned_data = {}
        for platform_name, titles in self.data.items():
            cleaned_data[platform_name] = {self.clean_title(title): tags for title, tags in titles.items()}
        with open(filename, "w") as file:
            yaml.dump(cleaned_data, file, default_flow_style=False, sort_keys=False)
        logger.debug("Data saved to YAML file: %s", filename)
