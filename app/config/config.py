import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Configuración de la API
    API_HOST = os.environ.get('API_HOST', '0.0.0.0')
    API_PORT = int(os.environ.get('API_PORT', 5001))
    
    # Configuración de Gradio
    GRADIO_HOST = os.environ.get('GRADIO_HOST', '0.0.0.0')
    GRADIO_PORT = int(os.environ.get('GRADIO_PORT', 7860))
    GRADIO_SHARE = os.environ.get('GRADIO_SHARE', 'False').lower() == 'true'
    
    # Configuración de Gemini AI
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash')
    GEMINI_MAX_TOKENS = int(os.environ.get('GEMINI_MAX_TOKENS', 1000000))
    GEMINI_TEMPERATURE = float(os.environ.get('GEMINI_TEMPERATURE', 0.4))

class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True

class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False

# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 