from flask import Blueprint, jsonify, request
import uuid
import base64
from app.models.gemini_model import gemini_model

# Crear Blueprint para endpoints de Gemini AI
gemini_bp = Blueprint('gemini', __name__)

@gemini_bp.route('/')
def gemini_home():
    """Información de la API de Gemini"""
    return jsonify({
        "message": "Gemini AI API endpoints disponibles",
        "version": "1.0.0",
        "model_info": gemini_model.get_model_info(),
        "endpoints": [
            "POST /ai/generate - Generar texto",
            "POST /ai/chat/create - Crear sesión de chat",
            "POST /ai/chat/<session_id>/message - Enviar mensaje al chat",
            "GET  /ai/chat/<session_id>/history - Obtener historial",
            "GET  /ai/chat/sessions - Listar sesiones",
            "DELETE /ai/chat/<session_id> - Eliminar sesión",
            "POST /ai/analyze-image - Analizar imagen",
            "GET  /ai/model-info - Información del modelo"
        ]
    })

@gemini_bp.route('/generate', methods=['POST'])
def generate_text():
    """Generar texto usando Gemini"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        prompt = data.get("prompt", "")
        system_instruction = data.get("system_instruction")
        
        if not prompt:
            return jsonify({
                "status": "error", 
                "message": "Prompt is required"
            }), 400
        
        result = gemini_model.generate_text(prompt, system_instruction)
        
        if result["status"] == "error":
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/chat/create', methods=['POST'])
def create_chat():
    """Crear nueva sesión de chat"""
    try:
        data = request.get_json() or {}
        session_id = data.get("session_id", str(uuid.uuid4()))
        system_instruction = data.get("system_instruction")
        
        result = gemini_model.create_chat_session(session_id, system_instruction)
        
        if result["status"] == "error":
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/chat/<session_id>/message', methods=['POST'])
def send_chat_message(session_id):
    """Enviar mensaje a una sesión de chat"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        message = data.get("message", "")
        if not message:
            return jsonify({
                "status": "error",
                "message": "Message is required"
            }), 400
        
        result = gemini_model.send_chat_message(session_id, message)
        
        if result["status"] == "error":
            return jsonify(result), 404 if "no encontrada" in result["message"] else 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/chat/<session_id>/history', methods=['GET'])
def get_chat_history(session_id):
    """Obtener historial de una sesión de chat"""
    try:
        result = gemini_model.get_chat_history(session_id)
        
        if result["status"] == "error":
            return jsonify(result), 404 if "no encontrada" in result["message"] else 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/chat/sessions', methods=['GET'])
def list_chat_sessions():
    """Listar todas las sesiones de chat"""
    try:
        result = gemini_model.list_chat_sessions()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/chat/<session_id>', methods=['DELETE'])
def delete_chat_session(session_id):
    """Eliminar una sesión de chat"""
    try:
        result = gemini_model.delete_chat_session(session_id)
        
        if result["status"] == "error":
            return jsonify(result), 404
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analizar imagen usando Gemini Vision"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Obtener imagen en base64
        image_base64 = data.get("image")
        prompt = data.get("prompt", "Describe esta imagen en detalle")
        
        if not image_base64:
            return jsonify({
                "status": "error",
                "message": "Image data is required"
            }), 400
        
        try:
            # Decodificar imagen de base64
            image_data = base64.b64decode(image_base64)
        except Exception:
            return jsonify({
                "status": "error",
                "message": "Invalid base64 image data"
            }), 400
        
        result = gemini_model.analyze_image(image_data, prompt)
        
        if result["status"] == "error":
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@gemini_bp.route('/model-info', methods=['GET'])
def get_model_info():
    """Obtener información del modelo Gemini"""
    try:
        info = gemini_model.get_model_info()
        return jsonify({
            "status": "success",
            "info": info
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Manejadores de errores específicos para Gemini
@gemini_bp.errorhandler(404)
def ai_not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint de AI no encontrado"
    }), 404

@gemini_bp.errorhandler(405)
def ai_method_not_allowed(error):
    return jsonify({
        "status": "error",
        "message": "Método no permitido para este endpoint de AI"
    }), 405 