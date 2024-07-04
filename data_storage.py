import yaml


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

    def save_to_yaml(self, filename):
        with open(filename, "w") as file:
            yaml.dump(self.data, file, default_flow_style=False, sort_keys=False)
