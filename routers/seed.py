# schemas.py - Modelos de Pydantic para la validación de datos

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from database import get_db
import models
from security import get_password_hash
import uuid
from typing import Dict, List

router = APIRouter(
    prefix="/seed",
    tags=["Datos de Prueba"]
)

# --- IDS FIJOS PARA GARANTIZAR IDEMPOTENCIA ---
SUPER_ADMIN_ROLE_ID = uuid.UUID('50000000-0000-0000-0000-000000000001')
CLIENTE_ADMIN_ROLE_ID = uuid.UUID('50000000-0000-0000-0000-000000000002')
VENDEDOR_ROLE_ID = uuid.UUID('50000000-0000-0000-0000-000000000003')

# IDs fijos para Clientes
CLIENTE_KARUMBE_ID = uuid.UUID('11111111-1111-1111-1111-111111111111')
CLIENTE_MARTILLO_ID = uuid.UUID('22222222-2222-2222-2222-222222222222')
CLIENTE_DULCESABOR_ID = uuid.UUID('33333333-3333-3333-3333-333333333333')
SUPER_ADMIN_CLIENTE_ID = uuid.UUID('00000000-0000-0000-0000-000000000000')

# IDs fijos para Usuarios
USER_SUPER_ADMIN_ID = uuid.UUID('eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee')
USER_ADMIN_KARUMBE_ID = uuid.UUID('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')
USER_VENDEDOR_KARUMBE_ID = uuid.UUID('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
USER_ADMIN_MARTILLO_ID = uuid.UUID('cccccccc-cccc-cccc-cccc-cccccccccccc')
USER_ADMIN_DULCESABOR_ID = uuid.UUID('dddddddd-dddd-dddd-dddd-dddddddddddd')


# Datos de Permisos (la clave es el código para referencia)
PERMISOS_DATA_LIST = [
    # Módulo Administración - Gestión de Clientes (Global, solo Super Admin)
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000001'), "codigo": "administracion.clientes.leer", "descripcion": "Ver lista y detalles de Clientes/Tenants.", "modulo": "Clientes (Global)"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000002'), "codigo": "administracion.clientes.crear", "descripcion": "Crear nuevos Clientes/Tenants.", "modulo": "Clientes (Global)"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000003'), "codigo": "administracion.clientes.actualizar", "descripcion": "Modificar datos de Clientes/Tenants.", "modulo": "Clientes (Global)"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000004'), "codigo": "administracion.clientes.eliminar", "descripcion": "Eliminar o desactivar Clientes/Tenants.", "modulo": "Clientes (Global)"},
    
    # Módulo Administración - Gestión de Usuarios (Tenant-Scope)
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000005'), "codigo": "administracion.usuarios.leer", "descripcion": "Ver lista y detalles de usuarios.", "modulo": "Usuarios"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000006'), "codigo": "administracion.usuarios.crear", "descripcion": "Crear nuevos usuarios.", "modulo": "Usuarios"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000007'), "codigo": "administracion.usuarios.actualizar", "descripcion": "Modificar datos de usuarios.", "modulo": "Usuarios"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000008'), "codigo": "administracion.usuarios.eliminar", "descripcion": "Desactivar o eliminar usuarios.", "modulo": "Usuarios"},
    
    # Módulo Administración - Gestión de Roles (Tenant-Scope)
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000009'), "codigo": "administracion.roles.leer", "descripcion": "Ver lista de roles y permisos.", "modulo": "Roles"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000000a'), "codigo": "administracion.roles.crear", "descripcion": "Crear nuevos roles.", "modulo": "Roles"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000000b'), "codigo": "administracion.roles.actualizar", "descripcion": "Modificar roles y asignar permisos.", "modulo": "Roles"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000000c'), "codigo": "administracion.roles.eliminar", "descripcion": "Eliminar roles (si no están asignados).", "modulo": "Roles"},
    
    # Módulo Inventario - Gestión de Productos
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000000d'), "codigo": "inventario.productos.leer", "descripcion": "Ver lista y detalles de productos y stock.", "modulo": "Inventario"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000000e'), "codigo": "inventario.productos.crear", "descripcion": "Crear nuevos productos.", "modulo": "Inventario"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000000f'), "codigo": "inventario.productos.actualizar", "descripcion": "Modificar datos de productos y stock.", "modulo": "Inventario"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000010'), "codigo": "inventario.productos.eliminar", "descripcion": "Eliminar o desactivar productos.", "modulo": "Inventario"},

    # Módulo Ventas
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000011'), "codigo": "ventas.leer", "descripcion": "Ver reportes y registros de ventas.", "modulo": "Ventas"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000012'), "codigo": "ventas.crear", "descripcion": "Registrar nuevas transacciones de venta.", "modulo": "Ventas"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000013'), "codigo": "ventas.actualizar", "descripcion": "Editar transacciones de venta.", "modulo": "Ventas"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000014'), "codigo": "ventas.eliminar", "descripcion": "Anular transacciones de venta.", "modulo": "Ventas"},
    
    # Módulo Compras
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000015'), "codigo": "compras.leer", "descripcion": "Ver registros de compras a proveedores.", "modulo": "Compras"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000016'), "codigo": "compras.crear", "descripcion": "Registrar nuevas transacciones de compra.", "modulo": "Compras"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000017'), "codigo": "compras.actualizar", "descripcion": "Modificar transacciones de compra.", "modulo": "Compras"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000018'), "codigo": "compras.eliminar", "descripcion": "Anular transacciones de compra.", "modulo": "Compras"},
    
    # Módulo Pedidos
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000019'), "codigo": "pedidos.leer", "descripcion": "Ver pedidos de clientes.", "modulo": "Pedidos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000001a'), "codigo": "pedidos.crear", "descripcion": "Registrar nuevos pedidos.", "modulo": "Pedidos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000001b'), "codigo": "pedidos.actualizar", "descripcion": "Actualizar estado de pedidos.", "modulo": "Pedidos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000001c'), "codigo": "pedidos.eliminar", "descripcion": "Cancelar pedidos.", "modulo": "Pedidos"},
    
    # Módulo Presupuestos
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000001d'), "codigo": "presupuestos.leer", "descripcion": "Ver cotizaciones y presupuestos.", "modulo": "Presupuestos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000001e'), "codigo": "presupuestos.crear", "descripcion": "Crear nuevas cotizaciones.", "modulo": "Presupuestos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-00000000001f'), "codigo": "presupuestos.actualizar", "descripcion": "Modificar presupuestos.", "modulo": "Presupuestos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000020'), "codigo": "presupuestos.eliminar", "descripcion": "Eliminar presupuestos.", "modulo": "Presupuestos"},

    # Módulo Contactos y Configuración (separamos de inventario)
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000021'), "codigo": "contactos.leer", "descripcion": "Ver lista de Clientes y Proveedores.", "modulo": "Contactos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000022'), "codigo": "contactos.crud", "descripcion": "CRUD de Clientes y Proveedores.", "modulo": "Contactos"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000023'), "codigo": "configuracion.leer", "descripcion": "Ver ajustes de configuración del cliente (moneda, impuestos).", "modulo": "Configuración"},
    {"id": uuid.UUID('40000000-0000-0000-0000-000000000024'), "codigo": "configuracion.actualizar", "descripcion": "Modificar ajustes de configuración del cliente.", "modulo": "Configuración"},
]


@router.post("/cargar-datos-prueba", summary="Carga inicial de clientes, usuarios, permisos y roles M:N.")
def cargar_datos_prueba(db: Session = Depends(get_db)):
    """
    Endpoint para cargar datos de prueba en la base de datos, asegurando
    la correcta inserción en las tablas de asociación 'permisos_roles' y 'roles_usuarios'.
    
    Implementa verificación de existencia (idempotencia) antes de la inserción masiva.
    """
    
    try:
        # --- VERIFICACIÓN DE IDEMPOTENCIA ---
        # Verificamos si la entidad principal (p. ej., un permiso o cliente) ya existe
        # Asumimos que si un permiso clave existe, el seed ya fue ejecutado.
        
        # 1. Comprobar si el primer permiso de la lista ya existe
        primer_permiso_id = PERMISOS_DATA_LIST[0]["id"]
        permiso_existente = db.execute(
            select(models.Permiso).where(models.Permiso.id == primer_permiso_id)
        ).scalar_one_or_none()
        
        if permiso_existente:
            # Si el permiso principal ya existe, retornamos el mensaje de éxito del seed anterior
            return {"mensaje": "Datos ya cargados previamente (Seed Idempotente)", "detalle": "Las entidades principales y las asociaciones M:N ya existían."}
        
        # -----------------------------------------------------------
        # SI NO EXISTE, PROCEDEMOS CON LA CARGA COMPLETA
        # -----------------------------------------------------------
        
        # --- 1. CARGAR PERMISOS ---
        permiso_objects: Dict[str, models.Permiso] = {}
        for p_data in PERMISOS_DATA_LIST:
            db_permiso = models.Permiso(**p_data)
            db.merge(db_permiso)
            permiso_objects[p_data["codigo"]] = db_permiso
        
        db.commit()
        
        
        # --- 2. CARGAR CLIENTES DE PRUEBA (DEBE SER ANTES QUE ROLES) ---
        clientes_prueba = [
            models.Cliente(id=SUPER_ADMIN_CLIENTE_ID, nombre="Global", subdominio="global", estado="activo", configuracion={}),
            models.Cliente(id=CLIENTE_KARUMBE_ID, nombre="Karumbe Pizzas", subdominio="karumbe", estado="activo", configuracion={"empresa": {"ruc": "12345678901", "moneda": "USD", "impuesto": 10}}),
            models.Cliente(id=CLIENTE_MARTILLO_ID, nombre="Ferretería El Martillo", subdominio="martillo", estado="activo", configuracion={"empresa": {"ruc": "98765432109", "moneda": "USD", "impuesto": 10}}),
            models.Cliente(id=CLIENTE_DULCESABOR_ID, nombre="Repostería Dulce Sabor", subdominio="dulcesabor", estado="activo", configuracion={"empresa": {"ruc": "55555555555", "moneda": "USD", "impuesto": 10}})
        ]
        
        for cliente in clientes_prueba:
            db.merge(cliente)
        db.commit()


        # --- 3. CARGAR ROLES (Tablas principales) ---
        # Ahora el cliente_id=CLIENTE_KARUMBE_ID ya existe en la tabla clientes
        roles_prueba = [
            models.Role(id=SUPER_ADMIN_ROLE_ID, cliente_id=None, nombre="Super Admin", descripcion="Administrador Global", es_rol_sistema=True),
            models.Role(id=CLIENTE_ADMIN_ROLE_ID, cliente_id=CLIENTE_KARUMBE_ID, nombre="Administrador", descripcion="Administrador de una empresa cliente", es_rol_sistema=True),
            models.Role(id=VENDEDOR_ROLE_ID, cliente_id=CLIENTE_KARUMBE_ID, nombre="Vendedor", descripcion="Rol básico para la operación de ventas", es_rol_sistema=True)
        ]
        
        for rol in roles_prueba:
            db.merge(rol) 
        db.commit()

        
        # --- 4. ASIGNAR PERMISOS A ROLES (Tabla de asociación: permisos_roles) ---
        
        rol_permiso_associations: List[models.RolPermiso] = []
        
        # 4.1 Super Admin: Permisos de administración global de Clientes/Tenants
        permisos_super_admin_codes = [
            "administracion.clientes.leer", 
            "administracion.clientes.crear", 
            "administracion.clientes.actualizar", 
            "administracion.clientes.eliminar"
        ]
        for code in permisos_super_admin_codes:
            rol_permiso_associations.append(
                models.RolPermiso(rol_id=SUPER_ADMIN_ROLE_ID, permiso_id=permiso_objects[code].id)
            )

        # 4.2 Admin Cliente: Acceso total al ámbito de su cliente (excluyendo gestión global de Clientes)
        permisos_admin_cliente_codes = [
            # Administración
            "administracion.usuarios.leer", "administracion.usuarios.crear", "administracion.usuarios.actualizar", "administracion.usuarios.eliminar",
            "administracion.roles.leer", "administracion.roles.crear", "administracion.roles.actualizar", "administracion.roles.eliminar",
            # Inventario
            "inventario.productos.leer", "inventario.productos.crear", "inventario.productos.actualizar", "inventario.productos.eliminar",
            # Ventas
            "ventas.leer", "ventas.crear", "ventas.actualizar", "ventas.eliminar",
            # Compras
            "compras.leer", "compras.crear", "compras.actualizar", "compras.eliminar",
            # Pedidos
            "pedidos.leer", "pedidos.crear", "pedidos.actualizar", "pedidos.eliminar",
            # Presupuestos
            "presupuestos.leer", "presupuestos.crear", "presupuestos.actualizar", "presupuestos.eliminar",
            # Configuración y Contactos
            "contactos.leer", "contactos.crud", "configuracion.leer", "configuracion.actualizar"
        ]
        for code in permisos_admin_cliente_codes:
            rol_permiso_associations.append(
                models.RolPermiso(rol_id=CLIENTE_ADMIN_ROLE_ID, permiso_id=permiso_objects[code].id)
            )

        # 4.3 Vendedor: Permisos básicos de operación (Ventas, Pedidos, Presupuestos y Contactos)
        permisos_vendedor_codes = [
            "ventas.crear", "ventas.leer",
            "pedidos.crear", "pedidos.leer", 
            "presupuestos.crear", "presupuestos.leer",
            "contactos.leer"
        ]
        for code in permisos_vendedor_codes:
            rol_permiso_associations.append(
                models.RolPermiso(rol_id=VENDEDOR_ROLE_ID, permiso_id=permiso_objects[code].id)
            )
            
        for rp_assoc in rol_permiso_associations:
            db.merge(rp_assoc) # Merge para manejar las claves compuestas
        db.commit()


        # --- 5. CARGAR USUARIOS DE PRUEBA ---
        usuarios_prueba = [
            models.Usuario(
                id=USER_SUPER_ADMIN_ID,
                cliente_id=None, 
                nombre_usuario="super_admin",
                email="super@admin.com",
                contraseña_hash=get_password_hash("12345"),
                nombre="Mr.",
                apellido="Global",
                estado="activo"
            ),
            models.Usuario(id=USER_ADMIN_KARUMBE_ID, cliente_id=CLIENTE_KARUMBE_ID, nombre_usuario="admin_karumbe", email="admin@karumbe.com", contraseña_hash=get_password_hash("12345"), nombre="Carlos", apellido="Rodríguez", estado="activo"),
            models.Usuario(id=USER_VENDEDOR_KARUMBE_ID, cliente_id=CLIENTE_KARUMBE_ID, nombre_usuario="vendedor_karumbe", email="vendedor@karumbe.com", contraseña_hash=get_password_hash("12345"), nombre="María", apellido="González", estado="activo"),
            models.Usuario(id=USER_ADMIN_MARTILLO_ID, cliente_id=CLIENTE_MARTILLO_ID, nombre_usuario="admin_martillo", email="admin@martillo.com", contraseña_hash=get_password_hash("12345"), nombre="Roberto", apellido="Silva", estado="activo"),
            models.Usuario(id=USER_ADMIN_DULCESABOR_ID, cliente_id=CLIENTE_DULCESABOR_ID, nombre_usuario="admin_dulcesabor", email="admin@dulcesabor.com", contraseña_hash=get_password_hash("12345"), nombre="Ana", apellido="Martínez", estado="activo")
        ]
        
        for usuario in usuarios_prueba:
            db.merge(usuario)
        db.commit()
        
        
        # --- 6. ASIGNAR ROLES A USUARIOS (Tabla de asociación: roles_usuarios) ---
        
        # Nota: El campo 'asignado_por' es obligatorio en UsuarioRole
        asignaciones = [
            # Super Admin
            models.UsuarioRole(usuario_id=USER_SUPER_ADMIN_ID, rol_id=SUPER_ADMIN_ROLE_ID, asignado_por=USER_SUPER_ADMIN_ID), 
            
            # Administradores de Cliente
            models.UsuarioRole(usuario_id=USER_ADMIN_KARUMBE_ID, rol_id=CLIENTE_ADMIN_ROLE_ID, asignado_por=USER_SUPER_ADMIN_ID),
            models.UsuarioRole(usuario_id=USER_ADMIN_MARTILLO_ID, rol_id=CLIENTE_ADMIN_ROLE_ID, asignado_por=USER_SUPER_ADMIN_ID),
            models.UsuarioRole(usuario_id=USER_ADMIN_DULCESABOR_ID, rol_id=CLIENTE_ADMIN_ROLE_ID, asignado_por=USER_SUPER_ADMIN_ID),
            
            # Vendedor
            models.UsuarioRole(usuario_id=USER_VENDEDOR_KARUMBE_ID, rol_id=VENDEDOR_ROLE_ID, asignado_por=USER_ADMIN_KARUMBE_ID)
        ]
        
        for asignacion in asignaciones:
            db.merge(asignacion)
            
        db.commit()


        return {
            "mensaje": "Seed de datos completado exitosamente",
            "permisos_creados": len(PERMISOS_DATA_LIST),
            "roles_creados": len(roles_prueba),
            "clientes_creados": len(clientes_prueba),
            "usuarios_creados": len(usuarios_prueba),
            "asignaciones_roles_usuarios": len(asignaciones)
        }
        
    except Exception as e:
        db.rollback()
        # Captura cualquier otro error, como un IntegrityError inesperado si los IDs fijos
        # ya existen por alguna razón no detectada por la verificación.
        raise HTTPException(status_code=500, detail=f"Error al cargar datos: {str(e)}")
