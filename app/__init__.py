from flask import Flask
from flask_cors import CORS
from app.config.config import Config


def create_app():
    """Factory function para crear la aplicación Flask"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Habilitar CORS
    CORS(app)

    # Registrar Blueprints (Controllers)
    from app.controllers.api_controller import api_bp
    from app.controllers.main_controller import main_bp
    from app.controllers.gemini_controller import gemini_bp
    from app.controllers.risk_chatbot_controller import risk_chatbot_bp
    from app.controllers.main_flow_controller import main_flow_bp
    from app.controllers.rag_controller import rag_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(gemini_bp, url_prefix='/ai')
    app.register_blueprint(risk_chatbot_bp, url_prefix='/risk-chat')
    app.register_blueprint(main_flow_bp)
    app.register_blueprint(rag_bp, url_prefix="/api/rag")

    return app