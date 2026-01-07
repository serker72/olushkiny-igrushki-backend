import yaml


def get_dict_from_yaml(file_name: str) -> dict:
    """Загрузка данных из файла YAML"""
    with open(file_name) as f:
        return yaml.safe_load(f)
