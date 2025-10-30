# microservicio_administracion/schemas/auth.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from schemas import usuarios

# -------------------------------------------------------------------
# SCHEMAS DE AUTENTICACIÓN Y SEGURIDAD (JWT)
# -------------------------------------------------------------------

class LoginRequest(BaseModel):
    """Datos esperados al intentar iniciar sesión."""
    nombre_usuario: str
    password: str

class TokenData(BaseModel):
    """
    Datos extraídos del payload del token JWT. 
    Usado por la dependencia de seguridad para obtener el usuario autenticado.
    """
    nombre_usuario: Optional[str] = None # Usado como 'sub' en el token
    user_id: Optional[UUID] = None       # El ID del usuario (UUID)
    cliente_id: Optional[UUID] = None    # El ID del cliente (UUID). Puede ser None
    roles: List[str] = []                # Nombres de los roles asignados al usuario
    permisos: List[str] = []             # Códigos de permisos asignados


class Token(BaseModel):
    """Datos que se envían al frontend después de un login exitoso."""
    access_token: str
    token_type: str = "bearer"
    # Incluye el esquema Usuario ya definido en la respuesta de login
    usuario: usuarios.Usuario 
    roles: List[str] = []       # Lista de nombres de roles para el frontend
    permisos: List[str] = []    # Lista de permisos para el frontend
    
# Actualizar las referencias después de definir todas las clases
Token.model_rebuild()