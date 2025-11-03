# schemas/compras_inventarios.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal

# -------------------------------------------------------------------
# SCHEMAS DE PROVEEDORES
# -------------------------------------------------------------------

class ProveedorBase(BaseModel):
    codigo_proveedor: str = Field(..., max_length=50)
    nombre: str = Field(..., max_length=100)
    ruc_ci: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    contacto_nombre: Optional[str] = Field(None, max_length=100)
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    dias_plazo_pago: int = Field(default=30)
    estado: str = Field(default='activo')
    notas: Optional[str] = None

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    codigo_proveedor: Optional[str] = Field(None, max_length=50)
    nombre: Optional[str] = Field(None, max_length=100)
    ruc_ci: Optional[str] = Field(None, max_length=20)
    direccion: Optional[str] = None
    telefono: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    contacto_nombre: Optional[str] = Field(None, max_length=100)
    contacto_telefono: Optional[str] = Field(None, max_length=20)
    dias_plazo_pago: Optional[int] = None
    estado: Optional[str] = None
    notas: Optional[str] = None

class Proveedor(ProveedorBase):
    id: UUID
    cliente_id: UUID
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE CATEGORÍAS DE PRODUCTOS
# -------------------------------------------------------------------

class CategoriaProductoBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = None
    categoria_padre_id: Optional[UUID] = None
    estado: str = Field(default='activo')

class CategoriaProductoCreate(CategoriaProductoBase):
    pass

class CategoriaProductoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=100)
    descripcion: Optional[str] = None
    categoria_padre_id: Optional[UUID] = None
    estado: Optional[str] = None

class CategoriaProducto(CategoriaProductoBase):
    id: UUID
    cliente_id: UUID
    fecha_creacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE PRODUCTOS
# -------------------------------------------------------------------

class ProductoBase(BaseModel):
    codigo_producto: str = Field(..., max_length=50)
    codigo_barras: Optional[str] = Field(None, max_length=100)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = None
    categoria_id: Optional[UUID] = None
    proveedor_id: Optional[UUID] = None
    unidad_medida: str = Field(default='unidad')
    precio_costo: Decimal = Field(default=0)
    precio_venta: Decimal = Field(default=0)
    stock_minimo: int = Field(default=0)
    stock_maximo: int = Field(default=0)
    impuestos: Optional[Dict[str, Any]] = None
    estado: str = Field(default='activo')

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(BaseModel):
    codigo_producto: Optional[str] = Field(None, max_length=50)
    codigo_barras: Optional[str] = Field(None, max_length=100)
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = None
    categoria_id: Optional[UUID] = None
    proveedor_id: Optional[UUID] = None
    unidad_medida: Optional[str] = None
    precio_costo: Optional[Decimal] = None
    precio_venta: Optional[Decimal] = None
    stock_minimo: Optional[int] = None
    stock_maximo: Optional[int] = None
    impuestos: Optional[Dict[str, Any]] = None
    estado: Optional[str] = None

class Producto(ProductoBase):
    id: UUID
    cliente_id: UUID
    stock_actual: int
    stock_reservado: int
    stock_disponible: int
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE ÓRDENES DE COMPRA
# -------------------------------------------------------------------

class OrdenCompraBase(BaseModel):
    numero_orden: str = Field(..., max_length=50)
    proveedor_id: UUID
    fecha_orden: date
    fecha_esperada_recepcion: Optional[date] = None
    estado: str = Field(default='pendiente')
    notas: Optional[str] = None

class OrdenCompraCreate(OrdenCompraBase):
    pass

class OrdenCompraUpdate(BaseModel):
    numero_orden: Optional[str] = Field(None, max_length=50)
    proveedor_id: Optional[UUID] = None
    fecha_orden: Optional[date] = None
    fecha_esperada_recepcion: Optional[date] = None
    estado: Optional[str] = None
    notas: Optional[str] = None

class OrdenCompra(OrdenCompraBase):
    id: UUID
    cliente_id: UUID
    usuario_creador_id: UUID
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE ITEMS DE ÓRDENES DE COMPRA
# -------------------------------------------------------------------

class OrdenCompraItemBase(BaseModel):
    producto_id: UUID
    cantidad_solicitada: Decimal
    precio_unitario: Decimal
    notas: Optional[str] = None

class OrdenCompraItemCreate(OrdenCompraItemBase):
    pass

class OrdenCompraItemUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    cantidad_solicitada: Optional[Decimal] = None
    precio_unitario: Optional[Decimal] = None
    notas: Optional[str] = None

class OrdenCompraItem(OrdenCompraItemBase):
    id: UUID
    orden_compra_id: UUID
    cantidad_recibida: Decimal
    impuestos: Decimal
    subtotal: Decimal
    total: Decimal
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE RECEPCIONES DE MERCADERÍA
# -------------------------------------------------------------------

class RecepcionMercaderiaBase(BaseModel):
    numero_recepcion: str = Field(..., max_length=50)
    orden_compra_id: UUID
    fecha_recepcion: date
    estado: str = Field(default='parcial')
    notas: Optional[str] = None

class RecepcionMercaderiaCreate(RecepcionMercaderiaBase):
    pass

class RecepcionMercaderiaUpdate(BaseModel):
    numero_recepcion: Optional[str] = Field(None, max_length=50)
    orden_compra_id: Optional[UUID] = None
    fecha_recepcion: Optional[date] = None
    estado: Optional[str] = None
    notas: Optional[str] = None

class RecepcionMercaderia(RecepcionMercaderiaBase):
    id: UUID
    cliente_id: UUID
    usuario_receptor_id: UUID
    fecha_creacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE ITEMS RECIBIDOS
# -------------------------------------------------------------------

class RecepcionItemBase(BaseModel):
    orden_compra_item_id: UUID
    producto_id: UUID
    cantidad_recibida: Decimal
    lote: Optional[str] = Field(None, max_length=100)
    fecha_vencimiento: Optional[date] = None
    precio_unitario: Optional[Decimal] = None
    ubicacion: Optional[str] = Field(None, max_length=100)

class RecepcionItemCreate(RecepcionItemBase):
    pass

class RecepcionItemUpdate(BaseModel):
    orden_compra_item_id: Optional[UUID] = None
    producto_id: Optional[UUID] = None
    cantidad_recibida: Optional[Decimal] = None
    lote: Optional[str] = Field(None, max_length=100)
    fecha_vencimiento: Optional[date] = None
    precio_unitario: Optional[Decimal] = None
    ubicacion: Optional[str] = Field(None, max_length=100)

class RecepcionItem(RecepcionItemBase):
    id: UUID
    recepcion_id: UUID
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE FACTURAS DE PROVEEDORES
# -------------------------------------------------------------------

class FacturaProveedorBase(BaseModel):
    proveedor_id: UUID
    numero_factura: str = Field(..., max_length=100)
    fecha_factura: date
    fecha_vencimiento: date
    estado: str = Field(default='pendiente')
    concepto: Optional[str] = None
    orden_compra_id: Optional[UUID] = None

class FacturaProveedorCreate(FacturaProveedorBase):
    pass

class FacturaProveedorUpdate(BaseModel):
    proveedor_id: Optional[UUID] = None
    numero_factura: Optional[str] = Field(None, max_length=100)
    fecha_factura: Optional[date] = None
    fecha_vencimiento: Optional[date] = None
    estado: Optional[str] = None
    concepto: Optional[str] = None
    orden_compra_id: Optional[UUID] = None

class FacturaProveedor(FacturaProveedorBase):
    id: UUID
    cliente_id: UUID
    subtotal: Decimal
    impuestos: Decimal
    total: Decimal
    saldo_pendiente: Decimal
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE PAGOS A PROVEEDORES
# -------------------------------------------------------------------

class PagoProveedorBase(BaseModel):
    factura_id: UUID
    numero_pago: str = Field(..., max_length=50)
    fecha_pago: date
    monto: Decimal
    metodo_pago: Optional[str] = Field(None, max_length=50)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    estado: str = Field(default='aplicado')
    notas: Optional[str] = None

class PagoProveedorCreate(PagoProveedorBase):
    pass

class PagoProveedorUpdate(BaseModel):
    factura_id: Optional[UUID] = None
    numero_pago: Optional[str] = Field(None, max_length=50)
    fecha_pago: Optional[date] = None
    monto: Optional[Decimal] = None
    metodo_pago: Optional[str] = Field(None, max_length=50)
    referencia_pago: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = None
    notas: Optional[str] = None

class PagoProveedor(PagoProveedorBase):
    id: UUID
    cliente_id: UUID
    usuario_creador_id: UUID
    fecha_creacion: datetime
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE AJUSTES DE INVENTARIO
# -------------------------------------------------------------------

class AjusteInventarioBase(BaseModel):
    numero_ajuste: str = Field(..., max_length=50)
    fecha_ajuste: date
    tipo_ajuste: str = Field(..., max_length=20)
    motivo: str = Field(..., max_length=100)
    estado: str = Field(default='pendiente')
    notas: Optional[str] = None

class AjusteInventarioCreate(AjusteInventarioBase):
    pass

class AjusteInventarioUpdate(BaseModel):
    numero_ajuste: Optional[str] = Field(None, max_length=50)
    fecha_ajuste: Optional[date] = None
    tipo_ajuste: Optional[str] = Field(None, max_length=20)
    motivo: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = None
    notas: Optional[str] = None

class AjusteInventario(AjusteInventarioBase):
    id: UUID
    cliente_id: UUID
    usuario_creador_id: UUID
    fecha_creacion: datetime
    fecha_aplicacion: Optional[datetime] = None
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE ITEMS DE AJUSTES DE INVENTARIO
# -------------------------------------------------------------------

class AjusteInventarioItemBase(BaseModel):
    producto_id: UUID
    cantidad_anterior: int
    cantidad_nueva: int
    motivo_detalle: Optional[str] = None

class AjusteInventarioItemCreate(AjusteInventarioItemBase):
    pass

class AjusteInventarioItemUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    cantidad_anterior: Optional[int] = None
    cantidad_nueva: Optional[int] = None
    motivo_detalle: Optional[str] = None

class AjusteInventarioItem(AjusteInventarioItemBase):
    id: UUID
    ajuste_id: UUID
    diferencia: int
    costo_promedio: Optional[Decimal] = None
    
    model_config = {'from_attributes': True}

# -------------------------------------------------------------------
# SCHEMAS DE ALERTAS DE STOCK
# -------------------------------------------------------------------

class AlertaStockBase(BaseModel):
    producto_id: UUID
    tipo_alerta: str = Field(..., max_length=20)
    nivel_actual: Decimal
    nivel_umbral: Decimal
    severidad: str = Field(default='medio')

class AlertaStockCreate(AlertaStockBase):
    pass

class AlertaStockUpdate(BaseModel):
    producto_id: Optional[UUID] = None
    tipo_alerta: Optional[str] = Field(None, max_length=20)
    nivel_actual: Optional[Decimal] = None
    nivel_umbral: Optional[Decimal] = None
    severidad: Optional[str] = None
    leida: Optional[bool] = None

class AlertaStock(AlertaStockBase):
    id: UUID
    cliente_id: UUID
    fecha_alerta: datetime
    leida: bool
    fecha_lectura: Optional[datetime] = None
    
    model_config = {'from_attributes': True}