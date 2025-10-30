from fastapi import FastAPI
from dotenv import load_dotenv
import os
import models # Esto carga las clases User, Role, etc.
from database import engine, get_db
from routers import usuarios, auth, seed, clientes, roles  

# --- Cargar la Configuración ---
load_dotenv(dotenv_path='config.env')

# --- Obtener Variables de Entorno ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")

# --- Inicialización de FastAPI ---
app = FastAPI(
    title="Microservicio de Administración y Seguridad (NexusGestión)",
    version="1.0.0",
    description=f"Gestión de Usuarios, Roles, Permisos y Logs de Auditoría. Conectado a PostgreSQL: {DB_NAME}",
)

# --- Configuración de CORS (Permite a Angular comunicarse con el Microservicio) ---
# Si tu frontend de Angular corre en http://localhost:4200 (el puerto típico)
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost",
    "http://localhost:4200",  # Permite que Angular se conecte
    # Se debe añadir aquí la URL de producción del frontend cuando esté lista
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],
)

# --- CREAR LAS TABLAS EN LA BASE DE DATOS ---
# Esto se ejecuta una vez al iniciar la aplicación.
# Le dice al motor de BD que cree todas las tablas definidas en models.py
models.Base.metadata.create_all(bind=engine) 

# --- REGISTRAR LOS ROUTERS DE LA API ---
# Añadir el router de clientes a la aplicación principal
app.include_router(clientes.router)

# Añadir el router de usuarios a la aplicación principal
app.include_router(usuarios.router)

# Añadir el token de autenticación a la aplicación principal
app.include_router(auth.router)

app.include_router(seed.router)

app.include_router(roles.router)

# --- Endpoint de Prueba ---
@app.get("/", tags= ['Prueba de conexión a BD'], summary="Prueba de Conexion")
def read_root():
    """Verificación básica de que el Microservicio está activo y lee el .env (config.env)."""
    return {
        "mensaje": "Microservicio de Administración y Seguridad activo.",
        "estado_bd": f"Conectado a la BD {DB_NAME} como usuario {DB_USER}"
    }
    pass