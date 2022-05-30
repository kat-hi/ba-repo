import logging


def extract(f):
    LOC = 0
    comments = 0
    with open(f) as file:
        try:
            content = file.readlines()
            for line in content:
                if line == '\n':
                    continue
                cleaned = line.replace('\n', '').strip()
                if cleaned.startswith('#'):
                    comments += 1
                elif cleaned.startswith('//'):
                    comments += 1
                elif cleaned.startswith('/*'):
                    comments += 1
                elif cleaned.startswith('%'):
                    comments += 1
                elif cleaned.startswith('REM'):
                    comments += 1
                elif cleaned.startswith('<!--'):
                    comments += 1
                elif cleaned.endswith('*/'):
                    comments += 1
                else:
                    LOC += 1
        except UnicodeDecodeError:
            logging.error(f"{f} fails")
    return {"LOC": LOC, "Comments": comments}
