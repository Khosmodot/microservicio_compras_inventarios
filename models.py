# models.py - Modelos de Base de Datos para el Microservicio de Administración y Seguridad

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, func
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
    # roles_asignados = relationship("UsuarioRole", back_populates="usuario")


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
    # usuarios_asignados = relationship("UsuarioRole", back_populates="rol")


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
    
    # Nota: la relación de 'asignado_por' requeriría manejo especial en SQLAlchemy
    # usuario = relationship("Usuario", back_populates="roles_asignados", foreign_keys=[usuario_id])
    # rol = relationship("Role", back_populates="usuarios_asignados")


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