from pydantic import BaseModel


class SkillMeta(BaseModel):
    name: str
    description: str
    path: str
    license: str | None = None
