#!/usr/bin/env python3
"""
Ejecutar solo la API Flask
Útil para desarrollo y testing de endpoints
"""

from app import create_app
from app.config.config import Config

def main():
    """Ejecutar solo Flask API"""
    print("=" * 50)
    print("🚀 INICIANDO FLASK API (Solo Backend)")
    print("=" * 50)
    print("📋 Arquitectura: MVC")
    print("🔧 Modo: API Only")
    print(f"🌐 URL: http://{Config.API_HOST}:{Config.API_PORT}")
    print(f"🔧 Debug: {Config.DEBUG}")
    print("=" * 50)
    
    # Crear y ejecutar la aplicación Flask
    flask_app = create_app()
    
    try:
        flask_app.run(
            host=Config.API_HOST,
            port=Config.API_PORT,
            debug=Config.DEBUG
        )
    except KeyboardInterrupt:
        print("\n🛑 API detenida por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 ¡Hasta luego!")

if __name__ == "__main__":
    main() 