# Aqui debe de ir la logica de activar y desactivar modulos
# Los registros se guardan en modulos_cliente
# la tabla modulos debe de cargarse automaticamente con modulos predefinidos

# utiliza algo similar a routers/seed.py para cargar los modulos predeterminados
# Ventas, Compras, Pedidos, Clientes Negocio, Inventario, administracion, presupuesto, reportes, Clientes(Para super administrador)

# luego la logica para asignar modulos_clientes usando los modulos cargados, ten en cuenta que los id se generan con UUID
# revisa  routers/clientes.py para entenderlo

# Creo que ya mencioné no toquetear models.py