# microservicio_administracion/routers/clientes.py

# Esto necesita implementar la logica de contactos de los clientes
# Debes de trabajar con la tabla contactos_clientes
# Trabaja tambien con schemas/clientes.py 


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import exc
from typing import List
from uuid import UUID

import models
from schemas import clientes, auth
from database import get_db
from security_dependencies import check_super_admin_role  

# Nota: La ruta GET /clientes/{id} no está protegida por ahora para permitir el flujo inicial.

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes (Solo Super Admin)"], 
)

# -------------------------------------------------------------------
# LÓGICA DE NEGOCIO (Funciones de utilidad para la BD)
# -------------------------------------------------------------------

def create_contacto(db: Session, cliente_id: UUID, contacto: clientes.ContactoClienteCreate):
    """
    Crea un nuevo contacto asociado a un cliente.
    """
    db_contacto = models.ContactoCliente(
        cliente_id=cliente_id,
        nombre_contacto=contacto.nombre_contacto,
        rol=contacto.rol,
        telefono=contacto.telefono,
        email=contacto.email
    )
    
    db.add(db_contacto)
    db.commit()
    db.refresh(db_contacto)
    return db_contacto

# -------------------------------------------------------------------
# ENDPOINTS DE LA API (CRUD COMPLETO PROTEGIDO)
# -------------------------------------------------------------------

# --- 1. CREAR CLIENTE (PROTEGIDO) ---
@router.post("/", 
    response_model=clientes.Cliente, 
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuevo cliente (empresa)",
    description="Permite registrar una nueva empresa/tenant en el sistema. REQUIERE ROL DE SUPER ADMINISTRADOR."
)
def create_cliente(
    cliente: clientes.ClienteCreate, 
    db: Session = Depends(get_db),
    auth_check: None = Depends(check_super_admin_role) # APLICAMOS PROTECCIÓN
):
    """
    Crea un nuevo registro en la tabla de clientes.
    """
    try:
        # 1. Verificar si el subdominio ya existe
        db_cliente_subdominio = db.query(models.Cliente).filter(models.Cliente.subdominio == cliente.subdominio).first()
        if db_cliente_subdominio:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El subdominio ya está registrado. Use otro nombre."
            )

        # 2. Crear la instancia del modelo SQLAlchemy
        # Asumimos que cliente.configuracion es parte de ClienteBase
        db_cliente = models.Cliente(
            nombre=cliente.nombre,
            subdominio=cliente.subdominio,
            configuracion=getattr(cliente, 'configuracion', None) # Manejo seguro de 'configuracion'
        )
        
        # 3. Guardar en la base de datos
        db.add(db_cliente)
        db.commit()
        db.refresh(db_cliente)
        
        return db_cliente
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad al crear el cliente.")


# --- 2. LEER TODOS LOS CLIENTES (PROTEGIDO) ---
@router.get("/", response_model=List[clientes.Cliente], summary="Obtiene la lista completa de todos los clientes/tenants.")
def leer_clientes(
    db: Session = Depends(get_db),
    auth_check: None = Depends(check_super_admin_role) # APLICAMOS PROTECCIÓN
):
    """
    Obtiene todos los Clientes del sistema (lista maestra de tenants).
    """
    return db.query(models.Cliente).all()


# --- 3. LEER CLIENTE POR ID (PROTEGIDO) ---
@router.get("/{cliente_id}", 
    response_model=clientes.Cliente,
    summary="Obtiene los detalles de un cliente por ID"
)
def leer_cliente_por_id(
    cliente_id: UUID, 
    db: Session = Depends(get_db),
    auth_check: None = Depends(check_super_admin_role) # APLICAMOS PROTECCIÓN
):
    """
    Busca y retorna un cliente por su ID (UUID).
    """
    db_cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    return db_cliente


# --- 4. ACTUALIZAR CLIENTE (PROTEGIDO) ---
@router.put("/{cliente_id}", response_model=clientes.Cliente, summary="Actualiza los datos de un cliente.")
def actualizar_cliente(
    cliente_id: UUID, 
    cliente_data: clientes.ClienteUpdate, 
    db: Session = Depends(get_db),
    auth_check: None = Depends(check_super_admin_role) # APLICAMOS PROTECCIÓN
):
    """
    Actualiza los datos del cliente, como nombre o estado (activo/suspendido).
    """
    db_cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    update_data = cliente_data.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(db_cliente, key, value)
        
    db.commit()
    db.refresh(db_cliente)
    return db_cliente


# --- 5. ELIMINAR/DESACTIVAR CLIENTE (ELIMINACIÓN LÓGICA, PROTEGIDO) ---
@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Desactiva lógicamente un cliente.")
def desactivar_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    auth_check: None = Depends(check_super_admin_role) # APLICAMOS PROTECCIÓN
):
    """
    Cambia el estado del cliente a 'suspendido' o 'inactivo'.
    """
    db_cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Implementación de Eliminación Lógica
    db_cliente.estado = 'suspendido' 
    
    db.commit()
    
    return


# -------------------------------------------------------------------
# ENDPOINTS DE CONTACTOS DE CLIENTES (RELACIÓN 1:N)
# -------------------------------------------------------------------

# --- 6. CREAR CONTACTO PARA UN CLIENTE (PROTEGIDO) ---
@router.post("/{cliente_id}/contactos", 
    response_model=clientes.ContactoCliente,
    status_code=status.HTTP_201_CREATED,
    summary="Añade un contacto al cliente especificado."
)
def add_contacto_to_cliente(
    cliente_id: UUID,
    contacto: clientes.ContactoClienteCreate,
    db: Session = Depends(get_db),
    auth_check: auth.TokenData = Depends(check_super_admin_role) # PROTECCIÓN
):
    """
    Crea un nuevo contacto asociado al cliente cuyo ID se proporciona en la ruta.
    """
    db_cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
    try:
        return create_contacto(db, cliente_id, contacto)
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error de integridad al crear el contacto.")

# --- 7. LEER TODOS LOS CONTACTOS DE UN CLIENTE (PROTEGIDO) ---
@router.get("/{cliente_id}/contactos",
    response_model=List[clientes.ContactoCliente],
    summary="Obtiene la lista de contactos de un cliente."
)
def get_contactos_by_cliente(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    auth_check: auth.TokenData = Depends(check_super_admin_role) # PROTECCIÓN de Super Admin
):
    """
    Retorna todos los contactos asociados a un cliente específico.
    """
    db_cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if db_cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    contactos = db.query(models.ContactoCliente).filter(
        models.ContactoCliente.cliente_id == cliente_id
    ).all()
    
    return contactos
