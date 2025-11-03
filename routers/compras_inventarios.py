# microservicio_administracion/routers/compras_inventarios.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import exc, and_
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

import models
from schemas import compras_inventarios, auth
from database import get_db
from security import get_current_user
from security_dependencies import require_permission

router = APIRouter(
    prefix="/compras-inventarios",
    tags=["Compras e Inventarios"]
)

# -------------------------------------------------------------------
# FUNCIONES DE UTILIDAD
# -------------------------------------------------------------------

def get_cliente_id_from_token(current_user: auth.TokenData) -> UUID:
    """Obtiene el cliente_id del token o lanza excepción si no tiene"""
    if not current_user.cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario debe estar asociado a un cliente para acceder a estas operaciones"
        )
    return current_user.cliente_id

def calcular_totales_orden_compra(db: Session, orden_compra_id: UUID):
    """Calcula y actualiza los totales de una orden de compra"""
    items = db.query(models.OrdenCompraItem).filter(
        models.OrdenCompraItem.orden_compra_id == orden_compra_id
    ).all()
    
    subtotal = sum(item.subtotal or Decimal('0') for item in items)
    impuestos = sum(item.impuestos or Decimal('0') for item in items)
    total = subtotal + impuestos
    
    orden_compra = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.id == orden_compra_id
    ).first()
    
    if orden_compra:
        orden_compra.subtotal = subtotal
        orden_compra.impuestos = impuestos
        orden_compra.total = total
        db.commit()

# -------------------------------------------------------------------
# ENDPOINTS DE PROVEEDORES
# -------------------------------------------------------------------

@router.post("/proveedores", 
             response_model=compras_inventarios.Proveedor,
             status_code=status.HTTP_201_CREATED,
             summary="Crear nuevo proveedor")
def crear_proveedor(
    proveedor_data: compras_inventarios.ProveedorCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.crear"))
):
    """Crea un nuevo proveedor para el cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar si el código de proveedor ya existe para este cliente
    proveedor_existente = db.query(models.Proveedor).filter(
        models.Proveedor.cliente_id == cliente_id,
        models.Proveedor.codigo_proveedor == proveedor_data.codigo_proveedor
    ).first()
    
    if proveedor_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un proveedor con ese código para este cliente"
        )
    
    try:
        db_proveedor = models.Proveedor(
            cliente_id=cliente_id,
            **proveedor_data.model_dump()
        )
        
        db.add(db_proveedor)
        db.commit()
        db.refresh(db_proveedor)
        return db_proveedor
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el proveedor"
        )

@router.get("/proveedores", 
            response_model=List[compras_inventarios.Proveedor],
            summary="Obtener lista de proveedores")
def obtener_proveedores(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.leer"))
):
    """Obtiene todos los proveedores del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    query = db.query(models.Proveedor).filter(
        models.Proveedor.cliente_id == cliente_id
    )
    
    if estado:
        query = query.filter(models.Proveedor.estado == estado)
    
    return query.order_by(models.Proveedor.nombre).all()

@router.get("/proveedores/{proveedor_id}",
            response_model=compras_inventarios.Proveedor,
            summary="Obtener proveedor por ID")
def obtener_proveedor(
    proveedor_id: UUID,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.leer"))
):
    """Obtiene un proveedor específico por ID"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    proveedor = db.query(models.Proveedor).filter(
        models.Proveedor.id == proveedor_id,
        models.Proveedor.cliente_id == cliente_id
    ).first()
    
    if not proveedor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado"
        )
    
    return proveedor

# -------------------------------------------------------------------
# ENDPOINTS DE CATEGORÍAS DE PRODUCTOS
# -------------------------------------------------------------------

@router.post("/categorias",
             response_model=compras_inventarios.CategoriaProducto,
             status_code=status.HTTP_201_CREATED,
             summary="Crear nueva categoría de producto")
def crear_categoria(
    categoria_data: compras_inventarios.CategoriaProductoCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.crear"))
):
    """Crea una nueva categoría de producto"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar si la categoría ya existe para este cliente
    categoria_existente = db.query(models.CategoriaProducto).filter(
        models.CategoriaProducto.cliente_id == cliente_id,
        models.CategoriaProducto.nombre == categoria_data.nombre
    ).first()
    
    if categoria_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre para este cliente"
        )
    
    try:
        db_categoria = models.CategoriaProducto(
            cliente_id=cliente_id,
            **categoria_data.model_dump()
        )
        
        db.add(db_categoria)
        db.commit()
        db.refresh(db_categoria)
        return db_categoria
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear la categoría"
        )

@router.get("/categorias",
            response_model=List[compras_inventarios.CategoriaProducto],
            summary="Obtener lista de categorías de productos")
def obtener_categorias(
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.leer"))
):
    """Obtiene todas las categorías de productos del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    return db.query(models.CategoriaProducto).filter(
        models.CategoriaProducto.cliente_id == cliente_id
    ).order_by(models.CategoriaProducto.nombre).all()

# -------------------------------------------------------------------
# ENDPOINTS DE PRODUCTOS
# -------------------------------------------------------------------

@router.post("/productos",
             response_model=compras_inventarios.Producto,
             status_code=status.HTTP_201_CREATED,
             summary="Crear nuevo producto")
def crear_producto(
    producto_data: compras_inventarios.ProductoCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.crear"))
):
    """Crea un nuevo producto en el inventario"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar si el código de producto ya existe para este cliente
    producto_existente = db.query(models.Producto).filter(
        models.Producto.cliente_id == cliente_id,
        models.Producto.codigo_producto == producto_data.codigo_producto
    ).first()
    
    if producto_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un producto con ese código para este cliente"
        )
    
    try:
        db_producto = models.Producto(
            cliente_id=cliente_id,
            stock_actual=0,
            stock_reservado=0,
            stock_disponible=0,
            **producto_data.model_dump()
        )
        
        db.add(db_producto)
        db.commit()
        db.refresh(db_producto)
        return db_producto
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el producto"
        )

@router.get("/productos",
            response_model=List[compras_inventarios.Producto],
            summary="Obtener lista de productos")
def obtener_productos(
    categoria_id: Optional[UUID] = Query(None, description="Filtrar por categoría"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.leer"))
):
    """Obtiene todos los productos del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    query = db.query(models.Producto).filter(
        models.Producto.cliente_id == cliente_id
    )
    
    if categoria_id:
        query = query.filter(models.Producto.categoria_id == categoria_id)
    
    if proveedor_id:
        query = query.filter(models.Producto.proveedor_id == proveedor_id)
    
    if estado:
        query = query.filter(models.Producto.estado == estado)
    
    return query.order_by(models.Producto.nombre).all()

@router.get("/productos/{producto_id}",
            response_model=compras_inventarios.Producto,
            summary="Obtener producto por ID")
def obtener_producto(
    producto_id: UUID,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.leer"))
):
    """Obtiene un producto específico por ID"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    producto = db.query(models.Producto).filter(
        models.Producto.id == producto_id,
        models.Producto.cliente_id == cliente_id
    ).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    return producto

# -------------------------------------------------------------------
# ENDPOINTS DE ÓRDENES DE COMPRA
# -------------------------------------------------------------------

@router.post("/ordenes-compra",
             response_model=compras_inventarios.OrdenCompra,
             status_code=status.HTTP_201_CREATED,
             summary="Crear nueva orden de compra")
def crear_orden_compra(
    orden_data: compras_inventarios.OrdenCompraCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.crear"))
):
    """Crea una nueva orden de compra"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar si el número de orden ya existe para este cliente
    orden_existente = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.cliente_id == cliente_id,
        models.OrdenCompra.numero_orden == orden_data.numero_orden
    ).first()
    
    if orden_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una orden de compra con ese número para este cliente"
        )
    
    try:
        db_orden = models.OrdenCompra(
            cliente_id=cliente_id,
            usuario_creador_id=current_user.user_id,
            subtotal=0,
            impuestos=0,
            total=0,
            **orden_data.model_dump()
        )
        
        db.add(db_orden)
        db.commit()
        db.refresh(db_orden)
        return db_orden
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear la orden de compra"
        )

@router.post("/ordenes-compra/{orden_id}/items",
             response_model=compras_inventarios.OrdenCompraItem,
             status_code=status.HTTP_201_CREATED,
             summary="Agregar item a orden de compra")
def agregar_item_orden_compra(
    orden_id: UUID,
    item_data: compras_inventarios.OrdenCompraItemCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.crear"))
):
    """Agrega un item a una orden de compra existente"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar que la orden existe y pertenece al cliente
    orden = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.id == orden_id,
        models.OrdenCompra.cliente_id == cliente_id
    ).first()
    
    if not orden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orden de compra no encontrada"
        )
    
    # Verificar que el producto existe y pertenece al cliente
    producto = db.query(models.Producto).filter(
        models.Producto.id == item_data.producto_id,
        models.Producto.cliente_id == cliente_id
    ).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    try:
        # Calcular subtotal y total del item
        subtotal = item_data.cantidad_solicitada * item_data.precio_unitario
        total = subtotal + (item_data.impuestos or Decimal('0'))
        
        db_item = models.OrdenCompraItem(
            orden_compra_id=orden_id,
            subtotal=subtotal,
            total=total,
            **item_data.model_dump()
        )
        
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        
        # Recalcular totales de la orden
        calcular_totales_orden_compra(db, orden_id)
        db.refresh(db_item.orden_compra)
        
        return db_item
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al agregar el item a la orden de compra"
        )

@router.get("/ordenes-compra",
            response_model=List[compras_inventarios.OrdenCompra],
            summary="Obtener lista de órdenes de compra")
def obtener_ordenes_compra(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.leer"))
):
    """Obtiene todas las órdenes de compra del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    query = db.query(models.OrdenCompra).filter(
        models.OrdenCompra.cliente_id == cliente_id
    )
    
    if estado:
        query = query.filter(models.OrdenCompra.estado == estado)
    
    if proveedor_id:
        query = query.filter(models.OrdenCompra.proveedor_id == proveedor_id)
    
    return query.order_by(models.OrdenCompra.fecha_orden.desc()).all()

# -------------------------------------------------------------------
# ENDPOINTS DE FACTURAS DE PROVEEDORES
# -------------------------------------------------------------------

@router.post("/facturas-proveedores",
             response_model=compras_inventarios.FacturaProveedor,
             status_code=status.HTTP_201_CREATED,
             summary="Crear nueva factura de proveedor")
def crear_factura_proveedor(
    factura_data: compras_inventarios.FacturaProveedorCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.crear"))
):
    """Crea una nueva factura de proveedor"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar si la factura ya existe para este proveedor
    factura_existente = db.query(models.FacturaProveedor).filter(
        models.FacturaProveedor.cliente_id == cliente_id,
        models.FacturaProveedor.proveedor_id == factura_data.proveedor_id,
        models.FacturaProveedor.numero_factura == factura_data.numero_factura
    ).first()
    
    if factura_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una factura con ese número para este proveedor"
        )
    
    try:
        db_factura = models.FacturaProveedor(
            cliente_id=cliente_id,
            subtotal=factura_data.subtotal or Decimal('0'),
            impuestos=factura_data.impuestos or Decimal('0'),
            total=factura_data.total or Decimal('0'),
            saldo_pendiente=factura_data.total or Decimal('0'),
            **factura_data.model_dump(exclude={'subtotal', 'impuestos', 'total'})
        )
        
        db.add(db_factura)
        db.commit()
        db.refresh(db_factura)
        return db_factura
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear la factura de proveedor"
        )

@router.get("/facturas-proveedores",
            response_model=List[compras_inventarios.FacturaProveedor],
            summary="Obtener lista de facturas de proveedores")
def obtener_facturas_proveedores(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    proveedor_id: Optional[UUID] = Query(None, description="Filtrar por proveedor"),
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("compras.leer"))
):
    """Obtiene todas las facturas de proveedores del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    query = db.query(models.FacturaProveedor).filter(
        models.FacturaProveedor.cliente_id == cliente_id
    )
    
    if estado:
        query = query.filter(models.FacturaProveedor.estado == estado)
    
    if proveedor_id:
        query = query.filter(models.FacturaProveedor.proveedor_id == proveedor_id)
    
    return query.order_by(models.FacturaProveedor.fecha_vencimiento).all()

# -------------------------------------------------------------------
# ENDPOINTS DE AJUSTES DE INVENTARIO
# -------------------------------------------------------------------

@router.post("/ajustes-inventario",
             response_model=compras_inventarios.AjusteInventario,
             status_code=status.HTTP_201_CREATED,
             summary="Crear nuevo ajuste de inventario")
def crear_ajuste_inventario(
    ajuste_data: compras_inventarios.AjusteInventarioCreate,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.actualizar"))
):
    """Crea un nuevo ajuste de inventario"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    # Verificar si el número de ajuste ya existe para este cliente
    ajuste_existente = db.query(models.AjusteInventario).filter(
        models.AjusteInventario.cliente_id == cliente_id,
        models.AjusteInventario.numero_ajuste == ajuste_data.numero_ajuste
    ).first()
    
    if ajuste_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un ajuste con ese número para este cliente"
        )
    
    try:
        db_ajuste = models.AjusteInventario(
            cliente_id=cliente_id,
            usuario_creador_id=current_user.user_id,
            **ajuste_data.model_dump()
        )
        
        db.add(db_ajuste)
        db.commit()
        db.refresh(db_ajuste)
        return db_ajuste
        
    except exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error al crear el ajuste de inventario"
        )

@router.get("/ajustes-inventario",
            response_model=List[compras_inventarios.AjusteInventario],
            summary="Obtener lista de ajustes de inventario")
def obtener_ajustes_inventario(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    tipo_ajuste: Optional[str] = Query(None, description="Filtrar por tipo de ajuste"),
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.leer"))
):
    """Obtiene todos los ajustes de inventario del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    query = db.query(models.AjusteInventario).filter(
        models.AjusteInventario.cliente_id == cliente_id
    )
    
    if estado:
        query = query.filter(models.AjusteInventario.estado == estado)
    
    if tipo_ajuste:
        query = query.filter(models.AjusteInventario.tipo_ajuste == tipo_ajuste)
    
    return query.order_by(models.AjusteInventario.fecha_ajuste.desc()).all()

# -------------------------------------------------------------------
# ENDPOINTS DE ALERTAS DE STOCK
# -------------------------------------------------------------------

@router.get("/alertas-stock",
            response_model=List[compras_inventarios.AlertaStock],
            summary="Obtener alertas de stock")
def obtener_alertas_stock(
    leida: Optional[bool] = Query(None, description="Filtrar por estado de lectura"),
    tipo_alerta: Optional[str] = Query(None, description="Filtrar por tipo de alerta"),
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.leer"))
):
    """Obtiene las alertas de stock del cliente actual"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    query = db.query(models.AlertaStock).filter(
        models.AlertaStock.cliente_id == cliente_id
    )
    
    if leida is not None:
        query = query.filter(models.AlertaStock.leida == leida)
    
    if tipo_alerta:
        query = query.filter(models.AlertaStock.tipo_alerta == tipo_alerta)
    
    return query.order_by(models.AlertaStock.fecha_alerta.desc()).all()

@router.patch("/alertas-stock/{alerta_id}/marcar-leida",
              response_model=compras_inventarios.AlertaStock,
              summary="Marcar alerta como leída")
def marcar_alerta_leida(
    alerta_id: UUID,
    db: Session = Depends(get_db),
    current_user: auth.TokenData = Depends(require_permission("inventario.productos.leer"))
):
    """Marca una alerta de stock como leída"""
    cliente_id = get_cliente_id_from_token(current_user)
    
    alerta = db.query(models.AlertaStock).filter(
        models.AlertaStock.id == alerta_id,
        models.AlertaStock.cliente_id == cliente_id
    ).first()
    
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada"
        )
    
    alerta.leida = True
    db.commit()
    db.refresh(alerta)
    
    return alerta