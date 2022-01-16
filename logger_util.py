import sys
from os import listdir, mkdir, path


class LogLevel:
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    STARTUP = "STARTUP"


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


def parse_log(log_file):
    parsed_logs = [[] for i in range(5)]
    with open(log_file, 'r') as f:
        for line in f.readlines():
            parts = line.split(':')
            for i in range(0, len(parts)):
                parts[i] = parts[i].strip()
            if parts[0] == LogLevel.ERROR:
                parsed_logs[0].append(":".join(parts[1:]))
            elif parts[0] == LogLevel.WARNING:
                parsed_logs[1].append(":".join(parts[1:]))
            elif parts[0] == LogLevel.INFO:
                parsed_logs[2].append(":".join(parts[1:]))
            elif parts[0] == LogLevel.STARTUP:
                parsed_logs[3].append(":".join(parts[1:]))
            else:
                parsed_logs[3].append(line)
    return parsed_logs
