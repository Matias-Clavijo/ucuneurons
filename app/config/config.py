import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Config:
    """Configuración base de la aplicación"""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

    # Configuración de la API
    API_HOST = os.environ.get("API_HOST", "0.0.0.0")
    API_PORT = int(os.environ.get("API_PORT", 5000))

    # Configuración de Gradio
    GRADIO_HOST = os.environ.get("GRADIO_HOST", "0.0.0.0")
    GRADIO_PORT = int(os.environ.get("GRADIO_PORT", 7860))
    GRADIO_SHARE = os.environ.get("GRADIO_SHARE", "False").lower() == "true"

    # Configuración de ChromaDB
    CHROMA_HOST = os.environ.get("CHROMA_HOST", "localhost")
    CHROMA_PORT = int(os.environ.get("CHROMA_PORT", 8000))
    CHROMA_USE_HTTP = os.environ.get("CHROMA_USE_HTTP", "True").lower() == "true"

    # Configuración de RAG
    RAG_COLLECTION_NAME = os.environ.get("RAG_COLLECTION_NAME", "documents")
    RAG_EMBEDDING_MODEL = os.environ.get("RAG_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    RAG_CHUNK_SIZE = int(os.environ.get("RAG_CHUNK_SIZE", 1000))
    RAG_CHUNK_OVERLAP = int(os.environ.get("RAG_CHUNK_OVERLAP", 200))

    # Configuración de Gemini
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-pro")

    # Configuración de archivos
    MAX_CONTENT_LENGTH = int(
        os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    )  # 16MB
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "./uploads")


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""

    DEBUG = True


class ProductionConfig(Config):
    """Configuración para producción"""

    DEBUG = False


# Diccionario de configuraciones
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
