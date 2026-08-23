from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    username: str
    role_id: int

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str