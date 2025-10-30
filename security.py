# microservicio_administracion/security.py
# Contiene la lógica para hashear contraseñas y gestionar tokens JWT

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Union, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from uuid import UUID
import os
from schemas import auth   


# Cargar variables de entorno para la clave secreta
load_dotenv(dotenv_path='config.env')

# La clave secreta de la aplicación. Es CRÍTICO que sea larga y aleatoria.
SECRET_KEY = os.getenv("SECRET_KEY", "TU_CLAVE_SECRETA_POR_DEFECTO_O_INSEGURA")
ALGORITHM = "HS256"
# El token expirará en 60 minutos
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

# Contexto de Hasheo para contraseñas (usa el algoritmo bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de seguridad para FastAPI (indica dónde buscar el token en el header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------

def truncate_password(password: str, max_length: int = 72) -> str:
    """Trunca la contraseña si excede el límite de bcrypt (72 bytes)"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > max_length:
        # Truncar en bytes y decodificar ignorando errores
        return password_bytes[:max_length].decode('utf-8', errors='ignore')
    return password

# -------------------------------------------------------------------
# FUNCIONES DE HASHEO DE CONTRASEÑAS
# -------------------------------------------------------------------


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña plana coincide con el hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Retorna el hash de una contraseña plana, manejando el límite de bcrypt."""
    try:
        truncated_password = truncate_password(password)
        return pwd_context.hash(truncated_password)
    except ValueError as e:
        # # Si falla, usar una contraseña por defecto más corta
        # if "password cannot be longer than 72 bytes" in str(e):
        #     return pwd_context.hash("default123")
        raise

# -------------------------------------------------------------------
# FUNCIONES DE GESTIÓN DE JWT
# -------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    
    # Usar datetime.now(timezone.utc) para consistencia
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire.timestamp()}) # Convertir a timestamp UNIX (entero)
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Any:
    """Decodifica y valida un token de acceso JWT, retornando el payload."""
    try:
        # Intenta decodificar el token usando la clave secreta y el algoritmo
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Si la decodificación falla (token inválido o expirado), retornar None
        return None
    except Exception:
        # Error genérico
        return None

# -------------------------------------------------------------------
# DEPENDENCIA DE FASTAPI (EL GUARDIÁN DE LAS RUTAS)
# -------------------------------------------------------------------

def get_current_user(token: str = Depends(oauth2_scheme)) -> auth.TokenData:
    """
    Dependencia de seguridad que se usa en los endpoints protegidos.
    1. Obtiene el token del header (OAuth2PasswordBearer).
    2. Decodifica el token y extrae los IDs.
    3. Retorna los datos esenciales del usuario logueado.
    """
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Decodificar y validar el token
    payload = decode_access_token(token)
    
    if payload is None:
        raise credentials_exception

    # 2. Extraer los IDs del payload
    user_id_str = payload.get("user_id")
    cliente_id_str = payload.get("cliente_id")
    roles = payload.get("roles", [])
    permisos = payload.get("permisos", []) 

    if user_id_str is None:
        raise credentials_exception

    # 3. Crear el objeto TokenData usando los UUIDs
    try:
        cliente_id_uuid = UUID(cliente_id_str) if cliente_id_str else None
        
        token_data = auth.TokenData(
            user_id=UUID(user_id_str), 
            cliente_id=cliente_id_uuid,
            roles=roles,
            permisos=permisos
        )
    except ValueError:
        # Si los strings de user_id o cliente_id no son UUIDs válidos
        raise credentials_exception
    
    return token_data

