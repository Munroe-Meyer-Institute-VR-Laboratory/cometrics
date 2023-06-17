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

    def get_fps(self):
        if self.config:
            if self.config['fps']:
                return float(self.config['fps'])

    def set_fps(self, new_fps):
        if self.config:
            if self.config['fps']:
                self.config['fps'] = new_fps
                self.save_config()
                return True
            else:
                return False

    def get_cwd(self):
        if self.config:
            return str(self.config['cwd'])

    def set_cwd(self, cwd):
        if self.config:
            self.config['cwd'] = cwd
            self.save_config()

    def get_e4(self):
        if self.config:
            return bool(self.config['enable-e4'])

    def set_e4(self, set_e4):
        if self.config:
            self.config['enable-e4'] = set_e4
            self.save_config()

    def get_woodway(self):
        if self.config:
            return bool(self.config['enable-woodway'])

    def set_woodway(self, set_woodway):
        if self.config:
            self.config['enable-woodway'] = set_woodway
            self.save_config()

    def get_ble(self):
        if self.config:
            return bool(self.config['enable-ble'])

    def set_ble(self, set_ble):
        if self.config:
            self.config['enable-ble'] = set_ble
            self.save_config()

    def get_review(self):
        if self.config:
            return bool(self.config['enable-review'])

    def set_review(self, set_review):
        if self.config:
            self.config['enable-review'] = set_review
            self.save_config()

    def get_clickmode(self):
        if self.config:
            return bool(self.config['enable-singleclick'])

    def set_clickmode(self, set_clickmode):
        if self.config:
            self.config['enable-singleclick'] = set_clickmode
            self.save_config()

    def get_woodway_a(self):
        if self.config:
            return str(self.config['woodway-a-sn'])

    def set_woodway_a(self, woodway_sn):
        if self.config:
            self.config['woodway-a-sn'] = woodway_sn
            self.save_config()

    def get_woodway_b(self):
        if self.config:
            return str(self.config['woodway-b-sn'])

    def set_woodway_b(self, woodway_sn):
        if self.config:
            self.config['woodway-b-sn'] = woodway_sn
            self.save_config()

    def get_auto_export(self):
        if self.config:
            return bool(self.config['auto-export'])

    def set_auto_export(self, export_option):
        if self.config:
            self.config['auto-export'] = export_option
            self.save_config()

    def get_use_count(self):
        if self.config:
            return int(self.config['use-count'])

    def increment_use_count(self):
        if self.config:
            self.config['use-count'] = int(self.config['use-count']) + 1
            self.save_config()
