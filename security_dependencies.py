from fastapi import Depends, HTTPException, status
from schemas import auth
from security import get_current_user 
from typing import Optional
from uuid import UUID

# Constante para el rol con bypass total
SUPER_ADMIN_ROLE_NAME = "Super Admin"

# -------------------------------------------------------------------
# LÓGICA DE VERIFICACIÓN DE PERMISOS (PARA RUTAS Multi-Tenant)
# -------------------------------------------------------------------

def require_permission(permission_code: str):
    """
    Dependencia de seguridad que verifica si el usuario tiene el permiso específico
    o si pertenece al rol de Super Administrador (bypass total).
    
    Uso: Depends(require_permission("administracion.roles.crear"))
    """
    
    def permission_checker(current_user: auth.TokenData = Depends(get_current_user)):
        """Función interna que realiza la verificación de autorización."""
        
        # 1. BYPASS para Super Administrador
        if SUPER_ADMIN_ROLE_NAME in current_user.roles:
            # El Super Administrador tiene acceso total y NO está obligado 
            # a tener un cliente_id asignado en el token.
            return current_user # <--- Retorno inmediato.
            
        # 2. VERIFICACIÓN ESTÁNDAR DE PERMISO (Solo para usuarios no-Super Admin)
        if permission_code not in current_user.permisos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail=f"Permiso denegado: Se requiere el permiso '{permission_code}' para esta acción."
            )
        
        # 3. VERIFICACIÓN DE TENANCY (Solo para usuarios no-Super Admin con permiso)
        # Es crucial que los usuarios operativos estén asignados a un cliente.
        if not current_user.cliente_id:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Acceso denegado: El usuario operativo no está asignado a un cliente (Tenant)."
            )

        return current_user

    return permission_checker

# -------------------------------------------------------------------
# LÓGICA DE VERIFICACIÓN DE ROL GLOBAL (PARA RUTAS DE CLIENTES/SISTEMA)
# -------------------------------------------------------------------

def check_super_admin_role(current_user: auth.TokenData = Depends(get_current_user)) -> None:
    """
    Dependencia que verifica si el usuario actual tiene el rol de Super Administrador.
    Esta dependencia debe usarse en rutas de gestión global (e.g., CRUD de Clientes).
    """
    if SUPER_ADMIN_ROLE_NAME not in current_user.roles:
        # Lanza una excepción si el usuario no tiene el rol de Super Administrador
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Acceso denegado. Se requiere el rol de Super Administrador para esta operación global."
        )
    
    # Si pasa, la función retorna el usuario (aunque no se use directamente) o None.
    return current_user
