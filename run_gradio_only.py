#!/usr/bin/env python3
"""
Ejecutar solo la interfaz Gradio
Requiere que la API Flask esté corriendo en otro proceso
"""

from app.views.gradio_interface import GradioInterface
from app.config.config import Config

def main():
    """Ejecutar solo interfaz Gradio"""
    print("=" * 50)
    print("🎨 INICIANDO GRADIO INTERFACE (Solo Frontend)")
    print("=" * 50)
    print("📋 Arquitectura: MVC")
    print("🔧 Modo: Interface Only")
    print(f"🎨 URL: http://{Config.GRADIO_HOST}:{Config.GRADIO_PORT}")
    print(f"🔗 API: http://{Config.API_HOST}:{Config.API_PORT}")
    print("=" * 50)
    print("⚠️  IMPORTANTE: Asegúrate de que la API Flask esté corriendo")
    print("   Ejecuta: python run_flask_only.py en otra terminal")
    print("=" * 50)
    
    try:
        # Crear y lanzar la interfaz Gradio
        gradio_interface = GradioInterface()
        gradio_interface.create_interface()
        
        gradio_interface.launch(
            server_name=Config.GRADIO_HOST,
            server_port=Config.GRADIO_PORT,
            share=Config.GRADIO_SHARE,
            show_error=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Interfaz detenida por el usuario")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        print("👋 ¡Hasta luego!")

if __name__ == "__main__":
    main() 