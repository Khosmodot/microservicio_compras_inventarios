# microservicio_administracion/routers/usuarios.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exc
from schemas import usuarios, auth
import models
from database import get_db
from security import get_password_hash, get_current_user
from security_dependencies import require_permission 
from uuid import UUID

# El módulo security se creará después, pero lo ponemos aquí para el plan
# import security 

router = APIRouter(
    prefix="/usuarios", 
    tags=["Usuarios y Gestión"]
)

# -------------------------------------------------------------------
# LÓGICA DE NEGOCIO (Aquí se reutiliza la lógica de la Clínica/Repostería)
# -------------------------------------------------------------------


def get_usuario_by_username_and_client(db: Session, nombre_usuario: str, cliente_id: UUID):
    """Busca un usuario por nombre de usuario y cliente_id."""
    return db.query(models.Usuario).filter(
        models.Usuario.nombre_usuario == nombre_usuario,
        models.Usuario.cliente_id == cliente_id
    ).first()

def get_usuario_by_id_and_client(db: Session, user_id: UUID, cliente_id: UUID):
    """Busca un usuario por ID y cliente_id."""
    return db.query(models.Usuario).filter(
        models.Usuario.id == user_id,
        models.Usuario.cliente_id == cliente_id
    ).first()

def create_usuario(db: Session, user: usuarios.UsuarioCreate):
    """
    Crea un nuevo usuario, hasheando la contraseña antes de guardar.
    """
    try:
    
        # 1. Hashear la contraseña con bcrypt
        hashed_password = get_password_hash(user.password) 
        
        # 2. Crear la instancia del modelo de SQLAlchemy
        db_usuario = models.Usuario(
            cliente_id=user.cliente_id,
            nombre_usuario=user.nombre_usuario,
            email=user.email,
            nombre=user.nombre,
            apellido=user.apellido,
            # Guardar el hash en lugar de la contraseña en texto plano
            contraseña_hash=hashed_password
        )
        
        # 3. Guardar y confirmar en la BD
        db.add(db_usuario)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario
    except exc.IntegrityError:
        db.rollback()
        # Maneja la colisión de nombre_usuario o email.
        raise HTTPException(status_code=400, detail="El nombre de usuario o email ya existen.")
    
# -------------------------------------------------------------------
# ENDPOINTS DE LA API (ACCESIBLES DESDE ANGULAR)
# -------------------------------------------------------------------

# --- 1. CREAR UN USUARIO ---
@router.post("/", response_model=usuarios.Usuario, 
             status_code=status.HTTP_201_CREATED,
             summary="Crea un nuevo usuario." 
             )
def crear_usuario(user_data: usuarios.UsuarioCreate, 
                db: Session = Depends(get_db),
                # REQUERIMIENTO: Solo usuarios autenticados pueden crear nuevos usuarios.
                current_user: auth.TokenData = Depends(require_permission("administracion.usuarios.crear")
                )): 
    """API para registrar un nuevo usuario, forzando la pertenencia al cliente logueado."""
    
    # SEGURIDAD CRÍTICA: Sobreescribir el cliente_id con el del token.
    # El require_permission ya verificó que este cliente_id existe para usuarios operativos.
    # Para Super Admin, cliente_id será None, lo cual debe ser manejado si Super Admin intenta crear
    # un usuario sin especificar cliente_id (aunque aquí ClienteCreate lo requiere en el body).
    if not current_user.cliente_id:
        # Esto solo se ejecutaría si un Super Admin usa este endpoint y ClienteCreate no tiene cliente_id opcional.
        # Asumimos que el Super Admin DEBE especificar cliente_id en el payload.
        pass
    else:
        # Fuerza la pertenencia al cliente del usuario logueado (Multi-Tenant)
        user_data.cliente_id = current_user.cliente_id
    
    # Si el Super Admin lo usa, user_data.cliente_id debe venir en el payload.
    # Para usuarios operativos, user_data.cliente_id se sobrescribe con el del token.
    
    db_user = get_usuario_by_username_and_client(db, user_data.nombre_usuario, user_data.cliente_id)
    if db_user:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
        
    return create_usuario(db=db, user=user_data)

# --- 2. LEER TODOS LOS USUARIOS ---
@router.get("/", response_model=list[usuarios.Usuario],  summary="Obtiene la lista completa de todos los usuarios." )
def leer_usuarios(db: Session = Depends(get_db),
                  current_user: auth.TokenData = Depends(require_permission("administracion.usuarios.leer")) # Esta dependencia verifica el permiso necesario y extrae los datos del usuario logueado
                    ): 
    """
    API para obtener todos los usuarios registrados.
    Solo retorna usuarios que pertenezcan al cliente_id del token actual (o todos si es Super Admin).
    """
    # FILTRADO MULTI-TENANT
    query = db.query(models.Usuario)
    
    if current_user.cliente_id:
        # Usuario operativo: solo ve usuarios de su propio cliente
        query = query.filter(models.Usuario.cliente_id == current_user.cliente_id)
        
    # Si es Super Admin, current_user.cliente_id es None, por lo que retorna TODOS los usuarios.
    return query.all()

# --- 3. LEER USUARIO POR ID ---
@router.get("/{user_id}", response_model=usuarios.Usuario, summary="Obtiene un usuario por ID.")
def leer_usuario_por_id(
    user_id: UUID, 
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("administracion.usuarios.leer"))
):
    """
    Busca y retorna un usuario por su ID. Solo si pertenece al cliente del token (o si es Super Admin).
    """
    
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # VERIFICACIÓN DE TENANCY: Si no es Super Admin, debe pertenecer al cliente.
    if current_user.cliente_id and db_user.cliente_id != current_user.cliente_id:
        raise HTTPException(status_code=403, detail="Permiso denegado: El usuario no pertenece a su cliente.")
        
    return db_user


# --- 4. ACTUALIZAR USUARIO ---
@router.put("/{user_id}", response_model=usuarios.Usuario, summary="Actualiza los datos de un usuario.")
def actualizar_usuario(
    user_id: UUID, 
    user_data: usuarios.UsuarioUpdate, 
    db: Session = Depends(get_db),
    # PERMISO REQUERIDO: administracion.usuarios.actualizar
    current_user: auth.TokenData = Depends(require_permission("administracion.usuarios.actualizar"))
):
    """
    Actualiza datos básicos de un usuario, respetando el límite Multi-Tenant.
    """
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # VERIFICACIÓN DE TENANCY: Si no es Super Admin, debe pertenecer al cliente.
    if current_user.cliente_id and db_user.cliente_id != current_user.cliente_id:
        raise HTTPException(status_code=403, detail="Permiso denegado: El usuario no pertenece a su cliente.")

    update_data = user_data.model_dump(exclude_unset=True)
    
    # Manejar el cambio de contraseña si está presente
    if 'password' in update_data and update_data['password']:
        update_data['contraseña_hash'] = get_password_hash(update_data.pop('password'))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

# --- 5. DESACTIVAR USUARIO (ELIMINACIÓN LÓGICA) ---
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desactiva lógicamente un usuario.")
def desactivar_usuario(
    user_id: UUID,
    db: Session = Depends(get_db),
    # PERMISO REQUERIDO: administracion.usuarios.eliminar
    current_user: auth.TokenData = Depends(require_permission("administracion.usuarios.eliminar"))
):
    """
    Desactiva lógicamente un usuario (cambia el estado a 'inactivo').
    """
    db_user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
    # VERIFICACIÓN DE TENANCY: Si no es Super Admin, debe pertenecer al cliente.
    if current_user.cliente_id and db_user.cliente_id != current_user.cliente_id:
        raise HTTPException(status_code=403, detail="Permiso denegado: El usuario no pertenece a su cliente.")

    # Implementación de Eliminación Lógica
    db_user.estado = 'inactivo' 
    
    db.commit()
    return