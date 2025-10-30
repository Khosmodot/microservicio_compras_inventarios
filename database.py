# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Cargar las variables de entorno para usar las credenciales de PostgreSQL
load_dotenv(dotenv_path='config.env')

# Obtener los parámetros de conexión desde config.env
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# 1. Definir la URL de Conexión a PostgreSQL (SQLAlchemy usa este formato)
# Formato: "postgresql://usuario:contraseña@host:puerto/nombre_bd"
SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# 2. Crear el Motor de la Base de Datos
# El 'engine' es el punto de conexión real con PostgreSQL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
    # La siguiente línea es útil para ver los comandos SQL que se ejecutan
    # , echo=True 
)

# 3. Crear una Sesión de Base de Datos
# 'SessionLocal' es la clase que se usará para crear sesiones de BD.
# Cada vez que la API reciba una petición, crearemos una instancia de esta clase.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Base Declarativa
# 'Base' es la clase base de la cual heredarán todos nuestros modelos de Python 
# (las tablas de la BD).
Base = declarative_base()


# --- Función de Dependencia para FastAPI (¡CRUCIAL!) ---
def get_db():
    """
    Función generadora para crear una sesión de BD por cada petición a la API.
    Asegura que la sesión se cierra correctamente después de la petición.
    """
    db = SessionLocal()
    try:
        yield db  # Retorna la sesión de BD
    finally:
        db.close() # Cierra la conexión después de que se usa