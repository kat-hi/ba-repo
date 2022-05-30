from datetime import datetime


def convert_gitdatestr_to_datetime(str):
    return datetime.strptime(str, '%Y-%m-%d %H:%M:%S %z')
