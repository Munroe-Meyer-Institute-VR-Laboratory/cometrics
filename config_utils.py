import yaml


class ConfigUtils:
    def __init__(self):
        self.config_file = 'config.yml'
        with open(self.config_file, 'r') as file:
            self.config = yaml.safe_load(file)

    def save_config(self):
        with open(self.config_file, 'w') as file:
            yaml.dump(self.config, file)

    def get_recent_projects(self):
        if self.config:
            return self.config['recent-projects']

    def set_recent_projects(self, projects):
        if self.config:
            self.config['recent-projects'] = projects
            self.save_config()

    def get_phases(self):
        if self.config:
            return self.config['phases']

    def set_screen_size(self, height, width):
        if self.config:
            self.config['window-size'] = [height, width]
            self.save_config()

    def get_screen_size(self):
        if self.config:
            return self.config['window-size']

    def get_data_folders(self):
        if self.config:
            return self.config['data-folders']

    def get_patient_concerns(self):
        if self.config:
            return self.config['patient-concerns']

    def get_first_time(self):
        if self.config:
            if self.config['first-time']:
                self.config['first-time'] = False
                self.save_config()
                return True
            else:
                return False

    def get_logs_dir(self):
        if self.config:
            if self.config['logs-dir']:
                return self.config['logs-dir']

    def set_logs_dir(self, new_logs_dir):
        if self.config:
            if self.config['logs-dir']:
                self.config['logs-dir'] = new_logs_dir
                self.save_config()
                return True
            else:
                return False

