from flask import Blueprint, jsonify, render_template
from app.models.data_model import data_model

# Crear Blueprint para rutas principales
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    """Ruta principal"""
    return jsonify({
        "message": "🚀 Bienvenido a la Web App MVC",
        "status": "active",
        "architecture": "Model-View-Controller",
        "endpoints": {
            "api": "/api/",
            "data": "/api/data",
            "process": "/api/process",
            "counter": "/api/counter",
            "stats": "/api/stats",
            "history": "/api/history"
        },
        "interfaces": {
            "gradio": "http://localhost:7860",
            "api": "http://localhost:5000"
        }
    })

@main_bp.route('/health')
def health_check():
    """Endpoint de salud"""
    stats = data_model.get_stats()
    return jsonify({
        "status": "healthy",
        "timestamp": stats["last_updated"],
        "data": stats
    })

@main_bp.route('/info')
def app_info():
    """Información de la aplicación"""
    return jsonify({
        "app_name": "Web App MVC",
        "version": "1.0.0",
        "architecture": "Flask + Gradio + MVC",
        "components": {
            "models": ["DataModel"],
            "views": ["GradioInterface"],
            "controllers": ["MainController", "ApiController"]
        }
    }) 