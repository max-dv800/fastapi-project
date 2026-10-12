from redis import from_url
from sqlalchemy import select

from app.core.database import SessionLocalCelery
from app.models import Task
from app.core.config import settings


cache = from_url(settings.redis_url)

def get_task_id(task_id):
    with SessionLocalCelery() as db:

        if cache.exists(task_id):
            data = cache.get(task_id)
            return data

        task_exists = db.scalar(select(Task).where(Task.task_id == task_id))

        return task_exists

def save_task_id(task_id):
    cache.set(task_id, "success", ex=7200)
    with SessionLocalCelery() as db:
        new_task = Task(task_id=task_id)
        db.add(new_task)
        db.commit()
       
