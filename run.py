#!/usr/bin/env python3
"""
Punto de entrada principal para la Web App MVC
Ejecuta Flask API y Gradio Interface usando arquitectura Model-View-Controller
"""

import threading
import time
import os
from app import create_app
from app.views.gradio_interface import GradioInterface
from app.config.config import Config

def run_flask_app():
    """Ejecutar la aplicación Flask en un hilo separado"""
    flask_app = create_app()
    flask_app.run(
        host=Config.API_HOST,
        port=Config.API_PORT,
        debug=False,  # Desactivar debug en threading
        use_reloader=False  # Evitar conflictos con threading
    )

def run_gradio_interface():
    """Ejecutar la interfaz Gradio"""
    # Esperar un momento a que Flask inicie
    time.sleep(2)
    
    gradio_interface = GradioInterface()
    gradio_interface.create_interface()
    
    print(f"🎨 Lanzando interfaz Gradio en http://{Config.GRADIO_HOST}:{Config.GRADIO_PORT}")
    gradio_interface.launch(
        server_name=Config.GRADIO_HOST,
        server_port=Config.GRADIO_PORT,
        share=Config.GRADIO_SHARE,
        show_error=True
    )

def main():
    """Función principal"""
    print("=" * 60)
    print("🚀 INICIANDO WEB APP MVC")
    print("=" * 60)
    print("📋 Arquitectura: Model-View-Controller")
    print("🔧 Backend: Flask API")
    print("🎨 Frontend: Gradio Interface")
    print("=" * 60)
    
    # Mostrar información de configuración
    print(f"🌐 Flask API: http://{Config.API_HOST}:{Config.API_PORT}")
    print(f"🎨 Gradio UI: http://{Config.GRADIO_HOST}:{Config.GRADIO_PORT}")
    print(f"🔧 Debug Mode: {Config.DEBUG}")
    print("=" * 60)
    
    try:
        # Iniciar Flask en un hilo separado
        print("🔄 Iniciando Flask API...")
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        
        # Dar tiempo a Flask para iniciar
        time.sleep(1)
        print("✅ Flask API iniciado correctamente")
        
        # Iniciar Gradio (bloquea el hilo principal)
        print("🔄 Iniciando interfaz Gradio...")
        run_gradio_interface()
        
    except KeyboardInterrupt:
        print("\n🛑 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
    finally:
        print("👋 ¡Hasta luego!")

if __name__ == "__main__":
    main() 