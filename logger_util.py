import sys
from os import listdir, mkdir, path


class CreateLogger:
    def __init__(self):
        sys.stdout = Log()
        sys.stderr = sys.stdout


class Log(object):
    def __init__(self):
        if not path.isdir('./logs'):
            mkdir('./logs')
        self.log_num = len(listdir('./logs'))
        self.orgstdout = sys.stdout
        self.log_name = "./logs/log_" + str(self.log_num) + ".txt"

    def write(self, msg):
        self.log = open(self.log_name, "a")
        self.orgstdout.write(msg)
        self.log.write(msg)
        self.log.close()

    def flush(self):
        pass
