from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core.auth import create_access_token
from app.core.exceptions import AppException
from app.schemas.auth import Token

router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    # Usually in production the users etc would be stored in a database and encrypted
    # But for this recruitment task I opted for just a simple hardcoded solution
    if form_data.username != "admin" or form_data.password != "secret":
        raise AppException(
            status_code=400,
            message="Incorrect username or password",
            code="AUTHENTICATION_ENDPOINT_FAIL",
        )

    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
