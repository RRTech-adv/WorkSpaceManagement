from pydantic import BaseModel
from typing import Dict, Optional


class ValidateTokenResponse(BaseModel):
    user_id: str
    email: str
    display_name: str
    pma_token: str
    roles: Dict[str, str]

