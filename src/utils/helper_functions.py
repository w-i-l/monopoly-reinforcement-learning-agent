import os

def format_path(path: str) -> str:
    if os.name == 'nt':
        return path.replace('/', '\\')
    elif os.name == 'posix':
        return path.replace('\\', '/')