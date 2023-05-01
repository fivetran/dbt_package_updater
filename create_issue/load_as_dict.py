import yaml

def load_yml(yml_name) -> dict:
    with open(yml_name + '.yml') as file:
        contents = yaml.load(file, Loader=yaml.FullLoader)
    return contents