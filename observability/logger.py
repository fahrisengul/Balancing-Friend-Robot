from datetime import datetime


def now_ts():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def info(msg: str):
    print(f"[{now_ts()}] {msg}")


def warn(msg: str):
    print(f"[{now_ts()}] [WARN] {msg}")


def error(msg: str):
    print(f"[{now_ts()}] [ERROR] {msg}")


def debug(msg: str, enabled: bool = False):
    if enabled:
        print(f"[{now_ts()}] [DEBUG] {msg}")
