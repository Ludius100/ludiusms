import os


bind = os.environ.get(
    "LMS_BIND",
    "127.0.0.1:8090",
)
workers = int(
    os.environ.get("LMS_WORKERS", "1")
)
threads = int(
    os.environ.get("LMS_THREADS", "4")
)
