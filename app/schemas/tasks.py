from pydantic import BaseModel, ConfigDict


class BaseTask(BaseModel):
    task_id: str


class TaskCreate(BaseTask):
    pass


class ResponseTask(BaseTask):
    model_config = ConfigDict(from_attributes=True)

    id: int
