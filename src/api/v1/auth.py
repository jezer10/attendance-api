from urllib.error import HTTPError, URLError
from urllib.request import Request as HTTPRequest, urlopen

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBasic,
    HTTPBasicCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, EmailStr
from supabase import Client, create_client
from supabase_auth.errors import AuthApiError
from typing import Annotated

from src.core.config import settings
from src.services.auth_service import AuthService


router = APIRouter()


security = HTTPBasic()
bearer_security = HTTPBearer(auto_error=False)

supabase: Client = create_client(settings.supabase_url, settings.supabase_key)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str | None = None


def get_bearer_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_security),
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Falta header Authorization")
    if not credentials.credentials:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return credentials.credentials


def get_current_user(token: str = Depends(get_bearer_token)) -> UserOut:
    """
    Esta función valida el token JWT enviado por el cliente.
    Espera un header:
        Authorization: Bearer <JWT>
    Usa Supabase para obtener al usuario asociado.
    Devuelve datos del user si todo está ok.
    """

    # Supabase puede decodificar el token y darte el user
    try:
        user_info = supabase.auth.get_user(token)
    except AuthApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        ) from exc
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo validar el token",
        ) from exc

    if user_info.user is None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Puedes leer más datos del perfil interno (tabla profiles) si quieres enriquecer
    try:
        profile_resp = (
            supabase.table("profiles")
            .select("*")
            .eq("id", user_info.user.id)
            .single()
            .execute()
        )
        if getattr(profile_resp, "error", None):
            # si falla el profile, igual devolvemos lo básico
            return UserOut(
                id=user_info.user.id, email=user_info.user.email, full_name=None
            )
        profile = profile_resp.data

        return UserOut(
            id=user_info.user.id,
            email=user_info.user.email,
            full_name=profile.get("full_name") if profile else None,
        )
    except Exception as e:
        print("Error al obtener usuario", e)
        return UserOut(id=user_info.user.id, email=user_info.user.email, full_name=None)


@router.post("/login")
def login(credentials: Annotated[HTTPBasicCredentials, Depends(security)]):

    try:
        login_resp = supabase.auth.sign_in_with_password(
            {"email": credentials.username, "password": credentials.password}
        )

        if login_resp.session is None:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        access_token = login_resp.session.access_token
        refresh_token = login_resp.session.refresh_token
        user_id = login_resp.user.id

        # Puedes también retornar info del perfil.
        return {
            "user_id": user_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except AuthApiError as e:
        print("Error en el inicio de sesión:", e)
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    except Exception as e:
        print("Error interno del servidor:", e)
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.post("/logout")
def logout(
    token: str = Depends(get_bearer_token),
    current_user: UserOut = Depends(get_current_user),
) -> dict[str, str]:
    logout_url = f"{settings.supabase_url}/auth/v1/logout"
    logout_request = HTTPRequest(
        logout_url,
        data=b"",
        method="POST",
        headers={
            "apikey": settings.supabase_key,
            "Authorization": f"Bearer {token}",
        },
    )

    try:
        with urlopen(logout_request, timeout=settings.request_timeout):
            pass
    except HTTPError as exc:
        if exc.code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo cerrar sesión en Supabase",
        ) from exc
    except URLError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Proveedor de autenticación no disponible",
        ) from exc

    return {
        "user_id": current_user.id,
        "detail": "Sesión cerrada correctamente",
    }


@router.get("/refresh")
def refresh_token(request: Request):
    refresh_token = request.query_params.get("token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token found")

    res = supabase.auth.refresh_session(refresh_token)
    new_access_token = res.session.access_token
    new_refresh_token = res.session.refresh_token

    return {
        "user_id": res.user.id,
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/token")
async def create_token(user_data: dict):
    """Create authentication token (for testing purposes)"""
    token = AuthService.create_access_token(data=user_data)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(current_user: UserOut = Depends(get_current_user)):
    """
    Ejemplo de endpoint privado.
    Solo entra alguien con Authorization: Bearer <token_válido>.
    """
    return current_user
