# models.py - Modelos de Base de Datos para el Microservicio de Compras e Inventarios

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
from database import Base
import datetime
import uuid

# ====================================================================
# TABLAS DE CORE MULTI-INQUILINO (MULTI-TENANT)
# ====================================================================

class Cliente(Base):
    """Representa a cada empresa o cliente (Pizzería, Ferretería, etc.)."""
    __tablename__ = "clientes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    subdominio = Column(String(50), unique=True, nullable=False)
    estado = Column(String(20), default='activo') # activo, suspendido, inactivo
    fecha_creacion = Column(DateTime, default=func.now())
    configuracion = Column(JSONB) # Almacenamiento de configuraciones específicas
    
    # Relaciones inversas (para acceder a sus usuarios, roles, etc.)
    usuarios = relationship("Usuario", back_populates="cliente")
    roles = relationship("Role", back_populates="cliente")
    modulos_activos = relationship("ModuloCliente", back_populates="cliente")
    contactos = relationship("ContactoCliente", back_populates="cliente")
    
    # Nuevas relaciones para compras e inventarios
    proveedores = relationship("Proveedor", back_populates="cliente")
    categorias_productos = relationship("CategoriaProducto", back_populates="cliente")
    productos = relationship("Producto", back_populates="cliente")
    ordenes_compra = relationship("OrdenCompra", back_populates="cliente")
    recepciones_mercaderia = relationship("RecepcionMercaderia", back_populates="cliente")
    facturas_proveedores = relationship("FacturaProveedor", back_populates="cliente")
    pagos_proveedores = relationship("PagoProveedor", back_populates="cliente")
    ajustes_inventario = relationship("AjusteInventario", back_populates="cliente")
    alertas_stock = relationship("AlertaStock", back_populates="cliente")


class ContactoCliente(Base):
    """Representa los contactos clave de la empresa cliente."""
    __tablename__ = "contactos_clientes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"))
    email = Column(String(100), nullable=False)
    telefono = Column(String(20))
    nombre_contacto = Column(String(100))
    rol = Column(String(50)) # propietario, gerente, técnico
    
    cliente = relationship("Cliente", back_populates="contactos")


# ====================================================================
# TABLAS DE USUARIOS Y PERFILES (REUTILIZACIÓN DE SEGURIDAD)
# ====================================================================

class Usuario(Base):
    """Modelo principal de usuarios del sistema."""
    __tablename__ = "usuarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=True)
    nombre_usuario = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    contraseña_hash = Column(String(255), nullable=False)
    nombre = Column(String(50))
    apellido = Column(String(50))
    estado = Column(String(20), default='activo') # activo, inactivo, bloqueado, eliminado
    ultimo_login = Column(DateTime)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    cliente = relationship("Cliente", back_populates="usuarios")
    perfil = relationship("PerfilUsuario", uselist=False, back_populates="usuario")
    
    # Nuevas relaciones para compras e inventarios
    ordenes_compra_creadas = relationship("OrdenCompra", foreign_keys="[OrdenCompra.usuario_creador_id]", back_populates="usuario_creador")
    recepciones_mercaderia = relationship("RecepcionMercaderia", foreign_keys="[RecepcionMercaderia.usuario_receptor_id]", back_populates="usuario_receptor")
    pagos_proveedores = relationship("PagoProveedor", foreign_keys="[PagoProveedor.usuario_creador_id]", back_populates="usuario_creador")
    ajustes_inventario = relationship("AjusteInventario", foreign_keys="[AjusteInventario.usuario_creador_id]", back_populates="usuario_creador")


class PerfilUsuario(Base):
    """Datos complementarios de los usuarios."""
    __tablename__ = "perfiles_usuarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Relación uno a uno
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True)
    url_avatar = Column(String(255))
    telefono = Column(String(20))
    departamento = Column(String(50))
    puesto = Column(String(50))
    
    usuario = relationship("Usuario", back_populates="perfil")


# ====================================================================
# TABLAS DE AUTORIZACIÓN (ROLES Y PERMISOS)
# ====================================================================

class Role(Base):
    """Roles definidos por el sistema o por el cliente."""
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"))
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text)
    es_rol_sistema = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=func.now())
    
    cliente = relationship("Cliente", back_populates="roles")
    permisos_asignados = relationship("RolPermiso", back_populates="rol")


class Permiso(Base):
    """Acciones granulares permitidas en el sistema (ventas.crear)."""
    __tablename__ = "permisos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo = Column(String(100), unique=True, nullable=False)
    descripcion = Column(Text)
    modulo = Column(String(50), nullable=False) # ventas, inventario, reportes
    
    roles = relationship("RolPermiso", back_populates="permiso")


class RolPermiso(Base):
    """Tabla de unión muchos a muchos entre Roles y Permisos."""
    __tablename__ = "permisos_roles"
    
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    permiso_id = Column(UUID(as_uuid=True), ForeignKey("permisos.id"), primary_key=True)
    
    rol = relationship("Role", back_populates="permisos_asignados")
    permiso = relationship("Permiso", back_populates="roles")


class UsuarioRole(Base):
    """Tabla de unión muchos a muchos entre Usuarios y Roles."""
    __tablename__ = "roles_usuarios"
    
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), primary_key=True)
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), primary_key=True)
    fecha_asignacion = Column(DateTime, default=func.now())
    asignado_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))


# ====================================================================
# TABLAS DE AUDITORÍA Y SEGURIDAD (REUTILIZACIÓN DE LOGS)
# ====================================================================

class RegistroAuditoria(Base):
    """Tabla de Logs de Auditoría (reutilización del concepto de Ferretería)."""
    __tablename__ = "registros_auditoria"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"))
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    accion = Column(String(100), nullable=False)
    tipo_recurso = Column(String(50))
    recurso_id = Column(UUID(as_uuid=True)) # ID del recurso afectado
    valores_anteriores = Column(JSONB)
    valores_nuevos = Column(JSONB)
    direccion_ip = Column(INET) # Tipo INET de PostgreSQL
    agente_usuario = Column(Text)
    fecha_hora = Column(DateTime, default=func.now())


class IntentoLogin(Base):
    """Registros de intentos de inicio de sesión."""
    __tablename__ = "intentos_login"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"))
    nombre_usuario = Column(String(100), nullable=False)
    direccion_ip = Column(INET)
    exito = Column(Boolean, default=False)
    fecha_intento = Column(DateTime, default=func.now())


class SesionUsuario(Base):
    """Registros de sesiones activas (para tokens o sesiones de larga duración)."""
    __tablename__ = "sesiones_usuarios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    token_sesion = Column(String(255), unique=True, nullable=False)
    expira_en = Column(DateTime, nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    ultima_actividad = Column(DateTime, default=func.now())


class TokenRecuperacion(Base):
    """Tokens para recuperar contraseñas."""
    __tablename__ = "tokens_recuperacion"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    token = Column(String(100), unique=True, nullable=False)
    expira_en = Column(DateTime, nullable=False)
    utilizado = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=func.now())


# ====================================================================
# TABLAS DE MODULARIDAD
# ====================================================================

class Modulo(Base):
    """Módulos centrales de la plataforma (Ventas, Compras, etc.)."""
    # Esta tabla se cargará de forma automatica con modulos preestablecidos
    __tablename__ = "modulos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(50), nullable=False)
    descripcion = Column(Text)
    icono = Column(String(100))
    ruta = Column(String(100)) # Ruta para la navegación en Angular
    activo = Column(Boolean, default=True)
    
    clientes_activos = relationship("ModuloCliente", back_populates="modulo")


class ModuloCliente(Base):
    """Tabla de relación para módulos activos por cliente."""
    __tablename__ = "modulos_clientes"
    
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), primary_key=True)
    modulo_id = Column(UUID(as_uuid=True), ForeignKey("modulos.id"), primary_key=True)
    activo = Column(Boolean, default=True)
    fecha_activacion = Column(DateTime, default=func.now())
    
    cliente = relationship("Cliente", back_populates="modulos_activos")
    modulo = relationship("Modulo", back_populates="clientes_activos")


# ====================================================================
# TABLAS DE COMPRAS E INVENTARIOS (NUEVAS)
# ====================================================================

class Proveedor(Base):
    """Tabla principal de proveedores."""
    __tablename__ = "proveedores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    codigo_proveedor = Column(String(50), nullable=False)
    nombre = Column(String(100), nullable=False)
    ruc_ci = Column(String(20))
    direccion = Column(Text)
    telefono = Column(String(20))
    email = Column(String(100))
    contacto_nombre = Column(String(100))
    contacto_telefono = Column(String(20))
    dias_plazo_pago = Column(Integer, default=30)
    estado = Column(String(20), default='activo') # activo, inactivo, suspendido
    notas = Column(Text)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    cliente = relationship("Cliente", back_populates="proveedores")
    productos = relationship("Producto", back_populates="proveedor")
    ordenes_compra = relationship("OrdenCompra", back_populates="proveedor")
    facturas_proveedores = relationship("FacturaProveedor", back_populates="proveedor")


class CategoriaProducto(Base):
    """Tabla de categorías de productos."""
    __tablename__ = "categorias_productos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    categoria_padre_id = Column(UUID(as_uuid=True), ForeignKey("categorias_productos.id"))
    estado = Column(String(20), default='activo')
    fecha_creacion = Column(DateTime, default=func.now())
    
    cliente = relationship("Cliente", back_populates="categorias_productos")
    productos = relationship("Producto", back_populates="categoria")
    subcategorias = relationship("CategoriaProducto", back_populates="categoria_padre", remote_side=[id])
    categoria_padre = relationship("CategoriaProducto", back_populates="subcategorias", remote_side=[id])


class Producto(Base):
    """Tabla principal de productos/inventario."""
    __tablename__ = "productos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    codigo_producto = Column(String(50), nullable=False)
    codigo_barras = Column(String(100))
    nombre = Column(String(200), nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(UUID(as_uuid=True), ForeignKey("categorias_productos.id"))
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("proveedores.id"))
    unidad_medida = Column(String(20), default='unidad') # unidad, kg, litro, etc.
    precio_costo = Column(Numeric(15, 2), default=0)
    precio_venta = Column(Numeric(15, 2), default=0)
    stock_minimo = Column(Integer, default=0)
    stock_maximo = Column(Integer, default=0)
    stock_actual = Column(Integer, default=0)
    stock_reservado = Column(Integer, default=0) # Para ventas pendientes
    stock_disponible = Column(Integer, default=0) # Calculado: actual - reservado
    impuestos = Column(JSONB) # Array de impuestos aplicables
    estado = Column(String(20), default='activo') # activo, inactivo, descontinuado
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    cliente = relationship("Cliente", back_populates="productos")
    categoria = relationship("CategoriaProducto", back_populates="productos")
    proveedor = relationship("Proveedor", back_populates="productos")
    ordenes_compra_items = relationship("OrdenCompraItem", back_populates="producto")
    recepciones_items = relationship("RecepcionItem", back_populates="producto")
    ajustes_inventario_items = relationship("AjusteInventarioItem", back_populates="producto")
    alertas_stock = relationship("AlertaStock", back_populates="producto")


class OrdenCompra(Base):
    """Tabla de órdenes de compra."""
    __tablename__ = "ordenes_compra"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    numero_orden = Column(String(50), nullable=False)
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("proveedores.id"))
    fecha_orden = Column(Date, nullable=False)
    fecha_esperada_recepcion = Column(Date)
    estado = Column(String(20), default='pendiente') # pendiente, parcial, recibida, cancelada
    subtotal = Column(Numeric(15, 2), default=0)
    impuestos = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    notas = Column(Text)
    usuario_creador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    cliente = relationship("Cliente", back_populates="ordenes_compra")
    proveedor = relationship("Proveedor", back_populates="ordenes_compra")
    usuario_creador = relationship("Usuario", back_populates="ordenes_compra_creadas", foreign_keys=[usuario_creador_id])
    items = relationship("OrdenCompraItem", back_populates="orden_compra")
    recepciones_mercaderia = relationship("RecepcionMercaderia", back_populates="orden_compra")
    facturas_proveedores = relationship("FacturaProveedor", back_populates="orden_compra")


class OrdenCompraItem(Base):
    """Tabla de items de órdenes de compra."""
    __tablename__ = "ordenes_compra_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orden_compra_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_compra.id"))
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"))
    cantidad_solicitada = Column(Numeric(10, 2), nullable=False)
    cantidad_recibida = Column(Numeric(10, 2), default=0)
    precio_unitario = Column(Numeric(15, 2), nullable=False)
    impuestos = Column(Numeric(15, 2), default=0)
    subtotal = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    notas = Column(Text)
    
    orden_compra = relationship("OrdenCompra", back_populates="items")
    producto = relationship("Producto", back_populates="ordenes_compra_items")
    recepciones_items = relationship("RecepcionItem", back_populates="orden_compra_item")


class RecepcionMercaderia(Base):
    """Tabla de recepciones de mercadería."""
    __tablename__ = "recepciones_mercaderia"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    orden_compra_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_compra.id"))
    numero_recepcion = Column(String(50), nullable=False)
    fecha_recepcion = Column(Date, nullable=False)
    estado = Column(String(20), default='parcial') # parcial, completa
    notas = Column(Text)
    usuario_receptor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    
    cliente = relationship("Cliente", back_populates="recepciones_mercaderia")
    orden_compra = relationship("OrdenCompra", back_populates="recepciones_mercaderia")
    usuario_receptor = relationship("Usuario", back_populates="recepciones_mercaderia", foreign_keys=[usuario_receptor_id])
    items = relationship("RecepcionItem", back_populates="recepcion")


class RecepcionItem(Base):
    """Tabla de items recibidos."""
    __tablename__ = "recepciones_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recepcion_id = Column(UUID(as_uuid=True), ForeignKey("recepciones_mercaderia.id"))
    orden_compra_item_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_compra_items.id"))
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"))
    cantidad_recibida = Column(Numeric(10, 2), nullable=False)
    lote = Column(String(100)) # Número de lote
    fecha_vencimiento = Column(Date)
    precio_unitario = Column(Numeric(15, 2))
    ubicacion = Column(String(100)) # Ubicación en almacén
    
    recepcion = relationship("RecepcionMercaderia", back_populates="items")
    orden_compra_item = relationship("OrdenCompraItem", back_populates="recepciones_items")
    producto = relationship("Producto", back_populates="recepciones_items")


class FacturaProveedor(Base):
    """Tabla de facturas de proveedores (cuentas por pagar)."""
    __tablename__ = "facturas_proveedores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    proveedor_id = Column(UUID(as_uuid=True), ForeignKey("proveedores.id"))
    numero_factura = Column(String(100), nullable=False)
    fecha_factura = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=False)
    estado = Column(String(20), default='pendiente') # pendiente, parcial, pagada, vencida
    subtotal = Column(Numeric(15, 2), default=0)
    impuestos = Column(Numeric(15, 2), default=0)
    total = Column(Numeric(15, 2), default=0)
    saldo_pendiente = Column(Numeric(15, 2), default=0)
    concepto = Column(Text)
    orden_compra_id = Column(UUID(as_uuid=True), ForeignKey("ordenes_compra.id")) # Relación opcional con OC
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_actualizacion = Column(DateTime, default=func.now(), onupdate=func.now())
    
    cliente = relationship("Cliente", back_populates="facturas_proveedores")
    proveedor = relationship("Proveedor", back_populates="facturas_proveedores")
    orden_compra = relationship("OrdenCompra", back_populates="facturas_proveedores")
    pagos = relationship("PagoProveedor", back_populates="factura")


class PagoProveedor(Base):
    """Tabla de pagos a proveedores."""
    __tablename__ = "pagos_proveedores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    factura_id = Column(UUID(as_uuid=True), ForeignKey("facturas_proveedores.id"))
    numero_pago = Column(String(50), nullable=False)
    fecha_pago = Column(Date, nullable=False)
    monto = Column(Numeric(15, 2), nullable=False)
    metodo_pago = Column(String(50)) # transferencia, efectivo, cheque, tarjeta
    referencia_pago = Column(String(100)) # Número de transferencia, cheque, etc.
    estado = Column(String(20), default='aplicado') # aplicado, anulado
    notas = Column(Text)
    usuario_creador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    
    cliente = relationship("Cliente", back_populates="pagos_proveedores")
    factura = relationship("FacturaProveedor", back_populates="pagos")
    usuario_creador = relationship("Usuario", back_populates="pagos_proveedores", foreign_keys=[usuario_creador_id])


class AjusteInventario(Base):
    """Tabla de ajustes de inventario."""
    __tablename__ = "ajustes_inventario"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    numero_ajuste = Column(String(50), nullable=False)
    fecha_ajuste = Column(Date, nullable=False)
    tipo_ajuste = Column(String(20), nullable=False) # entrada, salida, correccion
    motivo = Column(String(100), nullable=False) # daño, vencimiento, robo, corrección
    estado = Column(String(20), default='pendiente') # pendiente, aplicado, cancelado
    notas = Column(Text)
    usuario_creador_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())
    fecha_aplicacion = Column(DateTime)
    
    cliente = relationship("Cliente", back_populates="ajustes_inventario")
    usuario_creador = relationship("Usuario", back_populates="ajustes_inventario", foreign_keys=[usuario_creador_id])
    items = relationship("AjusteInventarioItem", back_populates="ajuste")


class AjusteInventarioItem(Base):
    """Tabla de items de ajustes de inventario."""
    __tablename__ = "ajustes_inventario_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ajuste_id = Column(UUID(as_uuid=True), ForeignKey("ajustes_inventario.id"))
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"))
    cantidad_anterior = Column(Integer, nullable=False)
    cantidad_nueva = Column(Integer, nullable=False)
    diferencia = Column(Integer, nullable=False) # Positivo para entradas, negativo para salidas
    costo_promedio = Column(Numeric(15, 2))
    motivo_detalle = Column(Text)
    
    ajuste = relationship("AjusteInventario", back_populates="items")
    producto = relationship("Producto", back_populates="ajustes_inventario_items")


class AlertaStock(Base):
    """Tabla para control de stock mínimo (alertas)."""
    __tablename__ = "alertas_stock"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    producto_id = Column(UUID(as_uuid=True), ForeignKey("productos.id"))
    tipo_alerta = Column(String(20), nullable=False) # stock_minimo, stock_maximo, vencimiento
    nivel_actual = Column(Numeric(10, 2), nullable=False)
    nivel_umbral = Column(Numeric(10, 2), nullable=False)
    severidad = Column(String(20), default='medio') # bajo, medio, alto, critico
    fecha_alerta = Column(DateTime, default=func.now())
    leida = Column(Boolean, default=False)
    fecha_lectura = Column(DateTime)
    
    cliente = relationship("Cliente", back_populates="alertas_stock")
    producto = relationship("Producto", back_populates="alertas_stock")