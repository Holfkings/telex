from pydantic import BaseModel


class UserProfile(BaseModel):
    username: str
    is_active: bool


def load_profile(data: dict) -> UserProfile:
    return UserProfile.model_validate(data)
