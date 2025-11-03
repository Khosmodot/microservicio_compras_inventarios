# main.py (actualización)

from fastapi import FastAPI
from dotenv import load_dotenv
import os
import models
from database import engine, get_db
from routers import usuarios, auth, seed, clientes, roles, modulos, logs, compras_inventarios

# --- Cargar la Configuración ---
load_dotenv(dotenv_path='config.env')

# --- Obtener Variables de Entorno ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")

# --- Inicialización de FastAPI ---
app = FastAPI(
    title="Microservicio de Compras e Inventarios (NexusGestión)",
    version="1.0.0",
    description=f"Gestión de Usuarios, Roles, Permisos y Logs de Auditoría. Conectado a PostgreSQL: {DB_NAME}",
)

# --- Configuración de CORS ---
from fastapi.middleware.cors import CORSMiddleware
origins = [
    "http://localhost",
    "http://localhost:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CREAR LAS TABLAS EN LA BASE DE DATOS ---
models.Base.metadata.create_all(bind=engine)

# --- REGISTRAR LOS ROUTERS DE LA API ---
app.include_router(clientes.router)
app.include_router(usuarios.router)
app.include_router(auth.router)
app.include_router(seed.router)
app.include_router(roles.router)
app.include_router(compras_inventarios.router)  # Nuevo router agregado

# --- Endpoint de Prueba ---
@app.get("/", tags=['Prueba de conexión a BD'], summary="Prueba de Conexion")
def read_root():
    """Verificación básica de que el Microservicio está activo y lee el .env (config.env)."""
    return {
        "mensaje": "Microservicio de Administración y Seguridad activo.",
        "estado_bd": f"Conectado a la BD {DB_NAME} como usuario {DB_USER}"
    }