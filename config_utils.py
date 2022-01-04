import yaml


class ConfigUtils:
    def __init__(self):
        with open('config.yml', 'r') as file:
            self.config = yaml.safe_load(file)

    def get_recent_projects(self):
        if self.config:
            return self.config['recent-projects']