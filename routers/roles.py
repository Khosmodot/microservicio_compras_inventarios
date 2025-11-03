# microservicio_administracion/routers/roles.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exc
from typing import List, Optional
from uuid import UUID

import models
from schemas import roles_y_permisos, auth
from database import get_db
from security import get_current_user
from security_dependencies import require_permission

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
    """
    if not current_user.cliente_id:
        # Super Admin puede acceder a todo
        return None
         
    return current_user.cliente_id

# -------------------------------------------------------------------
# ENDPOINTS DE PERMISOS (Solo Lectura, los permisos son de sistema)
# -------------------------------------------------------------------

@router.get("/permisos", response_model=List[roles_y_permisos.Permiso], summary="Obtiene la lista de todos los permisos definidos en el sistema.")
def read_all_permisos(
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(get_current_user)
):
    """
    Retorna todos los permisos disponibles, usados para configurar roles.
    """
    return db.query(models.Permiso).all()

# -------------------------------------------------------------------
# ENDPOINTS DE ROLES (CRUD Multi-Tenant)
# -------------------------------------------------------------------

# --- 1. CREAR ROL ---
@router.post("/", response_model=roles_y_permisos.Rol, status_code=status.HTTP_201_CREATED, summary="Crea un nuevo rol dentro del ámbito del cliente.")
def create_rol(
    rol_data: roles_y_permisos.RolCreate,
    permiso_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("administracion.roles.crear"))
):
    """
    Crea un nuevo rol asociado al cliente logueado y le asigna una lista de permisos.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    # Si no es Super Admin, usar el cliente_id del token
    if cliente_id is None and not any("Super Admin" in role for role in current_user.roles):
        raise HTTPException(status_code=403, detail="Se requiere cliente_id para crear roles")
    
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
            es_rol_sistema=False
        )
        
        # 3. Asignar permisos (Permisos_Roles)
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(permiso_ids)).all()
        
        # Verificar que todos los permisos existen
        if len(permisos) != len(permiso_ids):
            raise HTTPException(status_code=400, detail="Uno o más IDs de permiso no son válidos.")

        # Crear las relaciones de permisos
        for permiso in permisos:
            rol_permiso = models.RolPermiso(rol_id=db_rol.id, permiso_id=permiso.id)
            db.add(rol_permiso)
        
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
    current_user: auth.TokenData = Depends(require_permission("administracion.roles.leer"))
):
    """
    Retorna todos los roles asociados al cliente del token.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    # Si es Super Admin, mostrar todos los roles
    if cliente_id is None:
        roles = db.query(models.Role).options(joinedload(models.Role.permisos_asignados)).all()
    else:
        # Mostrar solo roles del cliente
        roles = db.query(models.Role).options(joinedload(models.Role.permisos_asignados)).filter(
            models.Role.cliente_id == cliente_id
        ).all()
    
    return roles

# --- 3. LEER ROL POR ID ---
@router.get("/{rol_id}", response_model=roles_y_permisos.Rol, summary="Obtiene un rol por su ID.")
def read_rol(
    rol_id: UUID, 
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("administracion.roles.leer"))
):
    """
    Busca y retorna un rol, solo si pertenece al cliente del token o es un rol de sistema.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)

    db_rol = db.query(models.Role).options(joinedload(models.Role.permisos_asignados)).filter(
        models.Role.id == rol_id
    ).first()
    
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
        
    # Verificar tenancy
    if cliente_id and db_rol.cliente_id != cliente_id:
        raise HTTPException(status_code=403, detail="Acceso denegado: El rol no pertenece a su cliente.")
        
    return db_rol

# --- 4. ACTUALIZAR ROL ---
@router.put("/{rol_id}", response_model=roles_y_permisos.Rol, summary="Actualiza el nombre/descripción y los permisos de un rol.")
def update_rol(
    rol_id: UUID, 
    rol_data: roles_y_permisos.RolUpdate,
    permiso_ids: Optional[List[UUID]] = None,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("administracion.roles.actualizar"))
):
    """
    Actualiza el nombre/descripción de un rol o su lista de permisos.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    db_rol = db.query(models.Role).filter(
        models.Role.id == rol_id
    ).first()

    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")
    
    # Verificar tenancy
    if cliente_id and db_rol.cliente_id != cliente_id:
        raise HTTPException(status_code=403, detail="Acceso denegado: El rol no pertenece a su cliente.")
    
    if db_rol.es_rol_sistema:
         raise HTTPException(status_code=403, detail="No se puede modificar un rol de sistema.")

    # 1. Actualizar campos de Rol
    update_data = rol_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rol, key, value)
        
    # 2. Actualizar Permisos si se proporcionan IDs
    if permiso_ids is not None:
        # Eliminar permisos actuales
        db.query(models.RolPermiso).filter(models.RolPermiso.rol_id == rol_id).delete()
        
        # Agregar nuevos permisos
        permisos = db.query(models.Permiso).filter(models.Permiso.id.in_(permiso_ids)).all()
        if len(permisos) != len(permiso_ids):
             raise HTTPException(status_code=400, detail="Uno o más IDs de permiso no son válidos.")
        
        for permiso in permisos:
            rol_permiso = models.RolPermiso(rol_id=rol_id, permiso_id=permiso.id)
            db.add(rol_permiso)
    
    db.commit()
    db.refresh(db_rol)
    return db_rol

# --- 5. ELIMINAR ROL ---
@router.delete("/{rol_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Elimina permanentemente un rol de cliente.")
def delete_rol(
    rol_id: UUID,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("administracion.roles.eliminar"))
):
    """
    Elimina un rol creado por el cliente. No se pueden eliminar roles de sistema.
    """
    cliente_id = check_client_admin_or_super_admin(current_user)
    
    db_rol = db.query(models.Role).filter(
        models.Role.id == rol_id
    ).first()
    
    if db_rol is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado.")

    # Verificar tenancy
    if cliente_id and db_rol.cliente_id != cliente_id:
        raise HTTPException(status_code=403, detail="Acceso denegado: El rol no pertenece a su cliente.")
        
    if db_rol.es_rol_sistema:
         raise HTTPException(status_code=403, detail="No se puede eliminar un rol de sistema.")
         
    # Eliminar relaciones de permisos primero
    db.query(models.RolPermiso).filter(models.RolPermiso.rol_id == rol_id).delete()
    
    # Eliminar el rol
    db.delete(db_rol)
    db.commit()
    return