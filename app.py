import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Importar configuración
from app.config.config import Config

# Importar controladores
from app.controllers.rag_faiss_controller import rag_faiss_bp
from app.controllers.gemini_controller import gemini_bp

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_app():
    """Crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configurar CORS
    CORS(app)

    # Registrar blueprints
    app.register_blueprint(rag_faiss_bp, url_prefix="/api/rag-faiss")
    app.register_blueprint(gemini_bp, url_prefix="/api/gemini")

    # Ruta de prueba de salud
    @app.route("/health")
    def health_check():
        return jsonify(
            {
                "status": "healthy",
                "message": "BASF RAG API está funcionando correctamente",
                "version": "2.0.0",
                "engines": ["FAISS + LangChain"],
                "models": ["Gemini 2.0 Flash", "Google Generative AI Embeddings"],
            }
        )

    # Ruta principal
    @app.route("/")
    def home():
        return jsonify(
            {
                "message": "BASF RAG System API",
                "version": "2.0.0",
                "description": "Sistema RAG para documentos de seguridad química de BASF",
                "engines": {"faiss": "/api/rag-faiss/"},
                "endpoints": {
                    "health": "/health",
                    "gemini": "/api/gemini/",
                    "rag_faiss": "/api/rag-faiss/",
                },
                "usage": {
                    "upload_files": "POST /api/rag-faiss/ingest con files[]",
                    "query": "POST /api/rag-faiss/query con JSON",
                    "search": "POST /api/rag-faiss/search con JSON",
                },
            }
        )

    return app


def main():
    """Función principal"""
    try:
        logger.info("🚀 Iniciando BASF RAG System...")

        # Crear aplicación Flask
        app = create_app()

        # Mostrar información de inicio
        logger.info("=" * 60)
        logger.info("🧪 BASF RAG SYSTEM - INICIADO CORRECTAMENTE")
        logger.info("=" * 60)
        logger.info(f"🌐 API REST: http://localhost:{Config.API_PORT}")
        logger.info("=" * 60)
        logger.info("📋 ENDPOINTS DISPONIBLES:")
        logger.info("   • FAISS RAG: /api/rag-faiss/")
        logger.info("   • Gemini AI: /api/gemini/")
        logger.info("   • Health Check: /health")
        logger.info("=" * 60)
        logger.info("🔧 MOTORES:")
        logger.info("   • FAISS + LangChain + Google Generative AI")
        logger.info("=" * 60)
        logger.info("📖 EJEMPLO DE USO:")
        logger.info("   curl -X POST http://localhost:5001/api/rag-faiss/ingest \\")
        logger.info("     -F 'files=@documento.pdf' \\")
        logger.info("     -F 'title=Mi Documento' \\")
        logger.info("     -F 'author=BASF'")
        logger.info("=" * 60)

        # Ejecutar servidor Flask
        app.run(
            host=Config.API_HOST,
            port=Config.API_PORT,
            debug=Config.DEBUG,
            threaded=True,
        )

    except Exception as e:
        logger.error(f"Error iniciando la aplicación: {str(e)}")
        raise


if __name__ == "__main__":
    main()
