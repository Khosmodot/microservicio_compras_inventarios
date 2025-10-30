# microservicio_administracion/schemas/clientes.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

# -------------------------------------------------------------------
# SCHEMAS BASE (CLIENTES)
# -------------------------------------------------------------------

class ClienteBase(BaseModel):
    """Esquema base para la creación de un cliente."""
    nombre: str
    subdominio: str
    configuracion: Optional[dict] = None # Permitimos pasar la configuración inicial

class ClienteCreate(ClienteBase):
    """Esquema de creación: Hereda de ClienteBase."""
    pass

class ClienteUpdate(BaseModel):
    """Esquema para actualizar datos de un cliente (todos los campos opcionales)."""
    nombre: Optional[str] = None
    subdominio: Optional[str] = None
    estado: Optional[str] = None # El estado se usa para la eliminación lógica ('suspendido')
    configuracion: Optional[dict] = None

class Cliente(ClienteBase):
    """Esquema de cliente completo, incluyendo campos de solo lectura devueltos por la BD."""
    id: UUID
    estado: str
    fecha_creacion: datetime

    # Configuración de Pydantic para manejar objetos de SQLAlchemy
    model_config = {'from_attributes': True}
    
# -------------------------------------------------------------------
# SCHEMAS DE CONTACTOS DE CLIENTES
# -------------------------------------------------------------------

class ContactoClienteBase(BaseModel):
    """Esquema base para la creación o actualización de un contacto, alineado con la tabla contactos_clientes."""
    email: EmailStr = Field(..., max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    nombre_contacto: str = Field(..., max_length=100, description="Nombre de la persona de contacto.")
    rol: Optional[str] = Field(None, max_length=50, description="Rol dentro de la empresa cliente (propietario, gerente, etc.).")

class ContactoClienteCreate(ContactoClienteBase):
    """Esquema para crear un nuevo contacto."""
    pass

class ContactoCliente(ContactoClienteBase):
    """Esquema completo del modelo de Contacto, incluyendo campos de solo lectura."""
    id: UUID
    cliente_id: UUID
    
    model_config = {'from_attributes': True}
