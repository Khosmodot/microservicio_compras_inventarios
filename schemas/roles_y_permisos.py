# microservicio_administracion/schemas/roles_y_permisos.py

from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

# -------------------------------------------------------------------
# SCHEMAS DE PERMISOS
# -------------------------------------------------------------------

class PermisoBase(BaseModel):
    """Esquema base para un permiso."""
    codigo: str
    descripcion: Optional[str] = None
    modulo: str

class Permiso(PermisoBase):
    """Esquema completo del permiso."""
    id: UUID
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE ROLES
# -------------------------------------------------------------------

class RolBase(BaseModel):
    """Esquema base para la creación/actualización de un rol."""
    nombre: str
    descripcion: Optional[str] = None
    # No se incluye cliente_id aquí, se asigna en el router
    # tampoco es_rol_sistema, que es solo para la lógica de seed

class RolCreate(RolBase):
    """Esquema para crear un nuevo rol."""
    pass

class RolUpdate(BaseModel):
    """Esquema para actualizar un rol (todo es opcional)."""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None

class Rol(RolBase):
    """Esquema completo del rol, devuelto por la API."""
    id: UUID
    cliente_id: Optional[UUID] = None # Puede ser None para roles de sistema
    es_rol_sistema: bool
    fecha_creacion: datetime
    
    # RELACIÓN: Lista de permisos asociados a este rol
    permisos: List[Permiso] = []

    model_config = {'from_attributes': True}
