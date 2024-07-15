import yaml
import re


class DataStorage:
    def __init__(self):
        self.data = {}

    def add_data(self, source, title, **tags):
        self.data.setdefault(source, {})[title] = tags

    def to_dict(self):
        return self.data

    def combine(self, data_storage):
        for source, titles in data_storage.data.items():
            self.data.setdefault(source, {}).update(titles)

    def clean_title(self, title):
        clean_title = re.sub(r'[^a-zA-Z0-9\s]', '', title)
        return clean_title

    def save_to_yaml(self, filename):
        cleaned_data = {}
        for source, titles in self.data.items():
            cleaned_data[source] = {self.clean_title(title): tags for title, tags in titles.items()}
        with open(filename, "w") as file:
            yaml.dump(cleaned_data, file, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    data_storage = DataStorage()
    data_storage.add_data('YouTube', 'Pydantic is all you need: Jason Liu', tag='tutorial')
    data_storage.add_data('YouTube', '[CHI 2024] &quot;We Need Structured Output&quot;: Towards User-centered Constraints on LLM Output', tag='conference')
    data_storage.add_data('YouTube', 'JSON Output from Mistral 7B LLM [LangChain, Ctransformers]', tag='example')
    data_storage.save_to_yaml('output.yaml')