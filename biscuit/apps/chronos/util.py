from datetime import datetime


def current_week():
    return int(datetime.now().strftime('%V'))
