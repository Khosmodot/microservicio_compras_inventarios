# microservicio_administracion/schemas/usuarios.py

from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID
from datetime import datetime

# -------------------------------------------------------------------
#  SCHEMAS DE USUARIOS
# -------------------------------------------------------------------

class UsuarioBase(BaseModel):
    """Esquema base que no incluye la contraseña."""
    nombre_usuario: str
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None

class UsuarioCreate(UsuarioBase):
    """Esquema para crear un nuevo usuario (requiere contraseña en texto plano)."""
    password: str
    # Cliente ID es necesario para el multi-tenant
    cliente_id: UUID
    
class UsuarioUpdate(UsuarioBase):
    """Esquema para actualizar datos (todos los campos opcionales)."""
    nombre_usuario: Optional[str] = None
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None

class Usuario(UsuarioBase):
    """Esquema del usuario devuelto por la API (Nunca incluye la contraseña hash)."""
    id: UUID
    cliente_id: Optional[UUID] = None
    estado: str
    fecha_creacion: datetime
    
    # class Config:
    #     from_attributes = True
    
    model_config = {'from_attributes': True}