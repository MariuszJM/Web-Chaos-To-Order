import pytest
import yaml
from src.data_storage import DataStorage

@pytest.fixture
def data_storage():
    return DataStorage()

def test_add_data(data_storage):
    data_storage.add_data("platform1", "title1", tag1="value1")
    assert "platform1" in data_storage.data
    assert "title1" in data_storage.data["platform1"]
    assert data_storage.data["platform1"]["title1"]["tag1"] == "value1"

def test_combine(data_storage):
    other_storage = DataStorage()
    other_storage.add_data("platform1", "title2", tag2="value2")
    data_storage.combine(other_storage)
    assert "platform1" in data_storage.data
    assert "title2" in data_storage.data["platform1"]
    assert data_storage.data["platform1"]["title2"]["tag2"] == "value2"

def test_add_data_list(data_storage):
    data_list = [
        {"title": "title3", "tag3": "value3"},
        {"title": "title4", "tag4": "value4"}
    ]
    data_storage.add_data_list("platform2", data_list)
    assert "platform2" in data_storage.data
    assert "title3" in data_storage.data["platform2"]
    assert data_storage.data["platform2"]["title3"]["tag3"] == "value3"

def test_to_dict(data_storage):
    data_storage.add_data("platform3", "title5", tag5="value5")
    data_dict = data_storage.to_dict()
    assert "platform3" in data_dict
    assert "title5" in data_dict["platform3"]
    assert data_dict["platform3"]["title5"]["tag5"] == "value5"

def test_clean_title(data_storage):
    dirty_title = "This! is a #dirty@ title?"
    clean_title = data_storage.clean_title(dirty_title)
    assert clean_title == "This is a dirty title"

def test_save_to_yaml(data_storage, tmp_path):
    data_storage.add_data("platform4", "title6", tag6="value6")
    file_path = tmp_path / "test.yaml"
    data_storage.save_to_yaml(file_path)
    with open(file_path, "r") as file:
        loaded_data = yaml.safe_load(file)
    assert "platform4" in loaded_data
    assert "title6" in loaded_data["platform4"]
    assert loaded_data["platform4"]["title6"]["tag6"] == "value6"
