import datetime
import sys
from os import listdir, mkdir, path
import wmi


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
    def __init__(self, log_path='./logs'):
        if not path.isdir(log_path):
            mkdir(log_path)
        self.log_num = len(listdir(log_path))
        self.orgstdout = sys.stdout
        self.log_name = f"{log_path}/log_" + str(self.log_num) + ".txt"

    def write(self, msg):
        self.log = open(self.log_name, "a")
        self.orgstdout.write(msg)
        self.log.write(msg)
        self.log.close()

    def flush(self):
        pass


def log_startup():
    print("STARTUP:", datetime.datetime.now().strftime("%c"))
    c = wmi.WMI()
    my_system = c.Win32_ComputerSystem()[0]
    print(f"STARTUP: Manufacturer - {my_system.Manufacturer}")
    print(f"STARTUP: Model - {my_system.Model}")
    print(f"STARTUP: Name - {my_system.Name}")
    print(f"STARTUP: NumberOfProcessors - {my_system.NumberOfProcessors}")
    print(f"STARTUP: SystemType - {my_system.SystemType}")
    print(f"STARTUP: SystemFamily - {my_system.SystemFamily}")


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
