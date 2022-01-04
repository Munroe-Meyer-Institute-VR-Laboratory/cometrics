import yaml


class ConfigUtils:
    def __init__(self):
        self.config_file = 'config.yml'
        with open(self.config_file, 'r') as file:
            self.config = yaml.safe_load(file)

    def get_recent_projects(self):
        if self.config:
            return self.config['recent-projects']

    def set_recent_projects(self, projects):
        if self.config:
            self.config['recent-projects'] = projects
            with open(self.config_file, 'w') as file:
                yaml.dump(self.config, file)

    def get_phases(self):
        if self.config:
            return self.config['phases']

    def set_screen_size(self, height, width):
        if self.config:
            self.config['window-size'] = [height, width]
            with open(self.config_file, 'w') as file:
                yaml.dump(self.config, file)

    def get_screen_size(self):
        if self.config:
            return self.config['window-size']

    def get_default_dirs(self):
        if self.config:
            return self.config['default-dirs']

    def get_data_folders(self):
        if self.config:
            return self.config['data-folders']