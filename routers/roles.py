# Como veras aqui no se encuentra nada campeón
# Yo que tu empezaria importando los schemas de roles/permisos 

# Los roles los debe de crear el cliente
# Los roles tienen permisos, los permisos los debe de elejir el cliente, ta tabla permisos ya tendrá valores preestablecidos
# Al final se guardará los registros en la tabla roles_usuarios 

# microservicio_administracion/routers/roles.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exc
from typing import List, Optional
from uuid import UUID

import models
from schemas import roles_y_permisos, auth
from database import get_db
from security import get_current_user # Importamos la dependencia para obtener el usuario actual

router = APIRouter(
    prefix="/roles", 
    tags=["Roles y Permisos (Multi-Tenant)"]
)



# -------------------------------------------------------------------
# FUNCIONES DE UTILIDAD Y NEGOCIO
# -------------------------------------------------------------------

def check_client_admin_or_super_admin(current_user: auth.TokenData) -> UUID:
    """
    Verifica que el usuario actual tenga permisos de administrador dentro
    de su cliente o sea Super Admin. 
    
    # NOTA: Por ahora, solo verifica autenticación y retorna cliente_id.
    # La verificación de rol ('Administrador') se añadiría aquí.
    """
    if not current_user.cliente_id:
         # Esta es una simplificación: Los Super Admin no tienen cliente_id, pero pueden acceder a todo.
         # En un sistema real, el Super Admin tendría un campo 'is_super_admin=True' en su token.
         # Dejamos la verificación de permisos en los endpoints.
         
         # Hacer esto conlleva a modificar la base de datos en usuarios y permitir que cliente_id tenga nulos (ya se hizo)  
         pass
         
    return current_user.cliente_id

# -------------------------------------------------------------------
# ENDPOINTS DE PERMISOS (Solo Lectura, los permisos son de sistema)
# -------------------------------------------------------------------

@router.get("/permisos", response_model=List[roles_y_permisos.Permiso], summary="Obtiene la lista de todos los permisos definidos en el sistema.")
def read_all_permisos(db: Session = Depends(get_db)):
    """
    Retorna todos los permisos disponibles, usados para configurar roles.
    No requiere autenticación ya que son datos estáticos del sistema,
    aunque en un entorno real podría estar restringido a administradores.
    """
    return db.query(models.Permiso).all()


# -------------------------------------------------------------------
# ENDPOINTS DE ROLES (CRUD Multi-Tenant)
# -------------------------------------------------------------------

# --- 1. CREAR ROL ---
@router.post("/", response_model=roles_y_permisos.Rol, status_code=status.HTTP_201_CREATED, summary="Crea un nuevo rol dentro del ámbito del cliente.")
def create_rol(
    rol_data: roles_y_permisos.RolCreate,
    permiso_ids: List[UUID], # IDs de los permisos a asignar
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(get_current_user)
):
    """
    Crea un nuevo rol asociado al cliente logueado y le asigna una lista de permisos.
    """
    cliente_id = check_client_admin_or_super_admin(current_user) # Verifica que tenga un cliente_id
    
    # 1. Verificar si el nombre del rol ya existe para este cliente
    db_rol_existente = db.query(models.Role).filter(
        models.Role.nombre == rol_data.nombre,
        models.Role.cliente_id == cliente_id
    ).first()
    
    if db_rol_existente:
        raise HTTPException(status_code=400, detail="Ya existe un rol con ese nombre para este cliente.")

    try:
        # 2. Crear la instancia del rol
        db_rol = models.Role(
            cliente_id=cliente_id,
            nombre=rol_data.nombre,
            descripcion=rol_data.descripcion,
            es_rol_sistema=False # Los roles creados por el cliente no son de sistema
        )
        
        # 3. Asignar permisos (Permisos_Roles)
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(permiso_ids)).all()
        
        # Si un ID no existe, SQLA lo manejará, pero podemos verificar proactivamente
        if len(permisos) != len(permiso_ids):
             raise HTTPException(status_code=400, detail="Uno o más IDs de permiso no son válidos.")

        db_rol.permisos_asignados = permisos
        
        # 4. Guardar en la base de datos
        db.add(db_rol)
        db.commit()
        db.refresh(db_rol)
        
        return db_rol
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad al crear el rol o asignar permisos.")


# --- 2. LEER TODOS LOS ROLES (Multi-Tenant) ---
@router.get("/", response_model=List[roles_y_permisos.Rol], summary="Obtiene todos los roles definidos para el cliente logueado.")
def read_all_roles(
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(get_current_user)
):
    """
    Retorna todos los roles asociados al cliente del token.
    Incluye los roles de sistema (cliente_id = NULL) que son visibles globalmente.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    # Retorna: Roles específicos del cliente (donde cliente_id == cliente_id) 
    # Y roles de sistema (donde cliente_id == NULL)
    roles = db.query(models.Role).options(joinedload(models.Role.permisos_asignados)).filter(
        (models.Role.cliente_id == cliente_id) | (models.Role.cliente_id.is_(None))
    ).all()
    
    return roles


# --- 3. LEER ROL POR ID ---
@router.get("/{rol_id}", response_model=roles_y_permisos.Rol, summary="Obtiene un rol por su ID.")
def read_rol(
    rol_id: UUID, 
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(get_current_user)
):
    """
    Busca y retorna un rol, solo si pertenece al cliente del token o es un rol de sistema.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)

    db_rol = db.query(models.Rol).options(joinedload(models.Rol.permisos)).filter(
        models.Rol.id == rol_id,
        (models.Rol.cliente_id == cliente_id) | (models.Rol.cliente_id.is_(None))
    ).first()
    
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado o acceso denegado.")
        
    return db_rol


# --- 4. ACTUALIZAR ROL ---
@router.put("/{rol_id}", response_model=roles_y_permisos.Rol, summary="Actualiza el nombre/descripción y los permisos de un rol.")
def update_rol(
    rol_id: UUID, 
    rol_data: roles_y_permisos.RolUpdate,
    permiso_ids: Optional[List[UUID]] = None, # Opcional para actualizar solo nombre
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(get_current_user)
):
    """
    Actualiza el nombre/descripción de un rol o su lista de permisos.
    Prohíbe la modificación de roles de sistema (es_rol_sistema = True).
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    db_rol = db.query(models.Rol).filter(
        models.Rol.id == rol_id,
        models.Rol.cliente_id == cliente_id
    ).first()

    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado o no puede ser modificado (es de sistema).")
    
    if db_rol.es_rol_sistema:
         raise HTTPException(status_code=403, detail="No se puede modificar un rol de sistema.")

    # 1. Actualizar campos de Rol
    update_data = rol_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rol, key, value)
        
    # 2. Actualizar Permisos si se proporcionan IDs
    if permiso_ids is not None:
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(permiso_ids)).all()
        if len(permisos) != len(permiso_ids):
             raise HTTPException(status_code=400, detail="Uno o más IDs de permiso no son válidos.")
        
        db_rol.permisos = permisos
    
    db.commit()
    db.refresh(db_rol)
    return db_rol


# --- 5. ELIMINAR ROL ---
@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Elimina permanentemente un rol de cliente.")
def delete_rol(
    rol_id: UUID,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(get_current_user)
):
    """
    Elimina un rol creado por el cliente. No se pueden eliminar roles de sistema.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    db_rol = db.query(models.Rol).filter(
        models.Rol.id == rol_id,
        models.Rol.cliente_id == cliente_id
    ).first()
    
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado o no puede ser eliminado (es de sistema).")

    if db_rol.es_rol_sistema:
         raise HTTPException(status_code=403, detail="No se puede eliminar un rol de sistema.")
         
    # La eliminación en cascada en la BD debe manejar la tabla permisos_roles
    db.delete(db_rol)
    db.commit()
    return
