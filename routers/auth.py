# microservicio_administracion/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
import uuid

# Importaciones absolutas para la lógica de la aplicación
from database import get_db
import models
from schemas import usuarios, auth
from security import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(
    prefix="/auth", 
    tags=["Login"]
)

# -------------------------------------------------------------------
# LÓGICA DE ROLES Y PERMISOS
# -------------------------------------------------------------------

def get_user_roles(db: Session, user_id: uuid.UUID) -> List[str]:
    """
    Consulta todos los nombres de los roles asignados a un usuario 
    a través de la tabla de asociación UsuarioRole (roles_usuarios).
    """
    # 1. Obtener los IDs de los roles asignados al usuario
    role_assignments = db.query(models.UsuarioRole.rol_id).filter(
        models.UsuarioRole.usuario_id == user_id
    ).all()
    
    if not role_assignments:
        return []

    role_ids = [assignment[0] for assignment in role_assignments]

    # 2. Obtener los nombres de los roles usando los IDs
    roles = db.query(models.Role.nombre).filter(
        models.Role.id.in_(role_ids)
    ).all()
    
    # 3. Retornar la lista de nombres de roles (ej: ["Super Admin", "Vendedor"])
    return [role[0] for role in roles]

def get_user_permissions(db: Session, user_id: uuid.UUID) -> List[str]:
    """
    Consulta todos los códigos de permiso únicos asignados a un usuario 
    a través de los roles que tiene asignados.
    """
    # 1. Obtener los IDs de los roles asignados al usuario
    role_ids_query = db.query(models.UsuarioRole.rol_id).filter(
        models.UsuarioRole.usuario_id == user_id
    )
    
    # 2. Obtener los IDs de los permisos asociados a esos roles
    permission_ids_query = db.query(models.RolPermiso.permiso_id).filter(
        models.RolPermiso.rol_id.in_(role_ids_query)
    ).distinct()
    
    # 3. Obtener los códigos de permiso usando los IDs
    permissions = db.query(models.Permiso.codigo).filter(
        models.Permiso.id.in_(permission_ids_query)
    ).all()
    
    # 4. Retornar la lista de códigos de permisos (ej: ["usuario:leer", "cliente:escribir"])
    return [p[0] for p in permissions]

# -------------------------------------------------------------------
# LÓGICA DE NEGOCIO DE AUTENTICACIÓN
# -------------------------------------------------------------------

def authenticate_user(db: Session, username: str, password: str):
    """
    Busca al usuario por nombre de usuario y verifica la contraseña.
    Retorna el objeto Usuario si las credenciales son válidas.
    """
    # 1. Buscar al usuario en la base de datos
    user = db.query(models.Usuario).filter(models.Usuario.nombre_usuario == username).first()
    
    # 2. Si el usuario no existe o la contraseña no es válida, retorna False
    if not user or not verify_password(password, user.contraseña_hash):
        return False
        
    # 3. Credenciales válidas
    return user

# -------------------------------------------------------------------
# ENDPOINT PRINCIPAL: LOGIN
# -------------------------------------------------------------------

@router.post("/login", response_model=auth.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Recibe credenciales (username/password) y retorna un token JWT.
    Utiliza el estándar OAuth2 para el formulario de login.
    """
    
    try:
        # Intentar autenticar al usuario
        user = authenticate_user(db, form_data.username, form_data.password)
        
        if not user:
            # Credenciales inválidas
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nombre de usuario o contraseña incorrectos",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # 1. Obtener los roles del usuario
        user_roles = get_user_roles(db, user.id)
        
        # 2. Obtener los permisos del usuario
        user_permissions = get_user_permissions(db, user.id) 

        # 3. Definir el tiempo de expiración del token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # 4. Crear el token JWT con la información del usuario
        access_token = create_access_token(
            data={
                "sub": user.nombre_usuario, # 'sub' es un estándar de JWT
                "user_id": str(user.id),
                "cliente_id": str(user.cliente_id) if user.cliente_id else None,
                "roles": user_roles,
                "permisos": user_permissions
            }, 
            expires_delta=access_token_expires
        )
        
        # 5. Retornar el token al cliente (Angular)
        return auth.Token(
            access_token=access_token,
            token_type="bearer",
            usuario=usuarios.Usuario.model_validate(user),
            roles=user_roles,
            permisos=user_permissions
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")