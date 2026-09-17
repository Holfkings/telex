from pydantic import BaseModel


class AppSettings(BaseModel):
    env: str
    debug: bool


def export_settings(cfg: AppSettings) -> dict:
    return cfg.model_dump()
