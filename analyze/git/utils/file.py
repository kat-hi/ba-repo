import os


def filepath_is_valid(relative_filepath):
    file_exclude_pattern = ['.zip', '.ttf', '.crushmap', 'osdmap', '.pkl', '.jpeg', '.gif', '.enc', '.mo', '.pb', '.gz',
                            '.exe', '.png', '.eot', '.woof', 'woff', '.mp3', '.ogg', '.jar', '.xcf',
                            '.jpg', '.pdf', '.idea', '.bin', '.rdb', '.xlsx', '.webm', '.DS_Store', '.sd', '.swf',
                            '.pyc', '.ico', '__pycache__', 'zips_input', '_macos' 'cp1252', 'migrations', 'utf-16',
                            'localanalyzer', 'gitrepo_analyzer', 'jira_analyzer', 'webfonts', 'encodings', 'cp850']
    if '.' not in relative_filepath:
        return False
    # avoid unwanted tracking
    for p in file_exclude_pattern:
        if p in relative_filepath:
            return False
    return True


def filepath_exists(relative_filepath, repository_path):
    filepath = os.path.join(repository_path, relative_filepath)
    return os.path.isfile(filepath)
