import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "audit_exec",
    broker=os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/1"),
    include=["execution.workers.specialists"],
)

celery_app.conf.task_default_queue = "audit_exec"
celery_app.conf.task_track_started = True
