from flask import Blueprint, jsonify, request
from app.models.data_model import data_model

api_bp = Blueprint('api', __name__)

@api_bp.route('/')
def api_home():
    """Información de la API"""
    return jsonify({
        "message": "API endpoints disponibles",
        "version": "1.0.0",
        "endpoints": [
            "GET  /api/data - Obtener todos los datos",
            "POST /api/data - Agregar mensaje",
            "POST /api/process - Procesar texto",
            "GET  /api/counter - Ver contador",
            "POST /api/counter - Incrementar contador",
            "DELETE /api/counter - Reiniciar contador",
            "GET  /api/stats - Estadísticas",
            "GET  /api/history - Historial de operaciones",
            "DELETE /api/history - Limpiar historial"
        ]
    })

@api_bp.route('/data', methods=['GET', 'POST'])
def handle_data():
    """Manejar datos"""
    if request.method == 'GET':
        try:
            data = data_model.get_all_data()
            return jsonify({
                "status": "success",
                "data": data
            })
        except Exception as e:
            return jsonify({
                "status": "error", 
                "message": str(e)
            }), 500
    
    elif request.method == 'POST':
        try:
            request_data = request.get_json()
            if not request_data:
                return jsonify({
                    "status": "error",
                    "message": "No data provided"
                }), 400
            
            message = request_data.get("message", "")
            if data_model.add_message(message):
                return jsonify({
                    "status": "success",
                    "message": "Mensaje agregado",
                    "data": {"message": message}
                })
            else:
                return jsonify({
                    "status": "error",
                    "message": "Error al agregar mensaje"
                }), 400
                
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            }), 500

@api_bp.route('/process', methods=['POST'])
def process_text():
    """Procesar texto"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Reconstruir el texto a partir del payload
        text_parts = [
            f"Chemicals: {request_data.get('chemicals', '')}",
            f"Place: {request_data.get('place', '')}",
            f"Materials: {request_data.get('materials', '')}",
            f"Frequency of use: {request_data.get('frequency', '')}",
            f"Environment: {request_data.get('environment', '')}",
            f"Process: {request_data.get('process', '')}",
            f"Additional Info: {request_data.get('additional_info', '')}"
        ]
        text = "\n".join(filter(lambda x: ': ' not in x or x.split(': ')[1], text_parts))

        if not text.strip():
            return jsonify({
                "status": "error", 
                "message": "All fields are empty"
            }), 400

        image_base64 = request_data.get('image_base64')
        result = data_model.process_text(text, image_base64)
        
        if "error" in result:
            return jsonify({
                "status": "error",
                "message": result["error"]
            }), 400
        
        return jsonify({
            "status": "success",
            "result": result
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/counter', methods=['GET', 'POST', 'DELETE'])
def handle_counter():
    """Manejar contador"""
    try:
        if request.method == 'GET':
            counter_value = data_model.get_counter()
            return jsonify({
                "status": "success",
                "counter": counter_value
            })
        
        elif request.method == 'POST':
            new_value = data_model.increment_counter()
            return jsonify({
                "status": "success",
                "counter": new_value,
                "action": "incremented"
            })
        
        elif request.method == 'DELETE':
            reset_value = data_model.reset_counter()
            return jsonify({
                "status": "success", 
                "counter": reset_value,
                "action": "reset"
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Obtener estadísticas"""
    try:
        stats = data_model.get_stats()
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api_bp.route('/history', methods=['GET', 'DELETE'])
def handle_history():
    """Manejar historial"""
    try:
        if request.method == 'GET':
            history = data_model.get_history()
            return jsonify({
                "status": "success",
                "history": history,
                "count": len(history)
            })
        
        elif request.method == 'DELETE':
            data_model.clear_history()
            return jsonify({
                "status": "success",
                "message": "Historial limpiado"
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Manejador de errores para el Blueprint
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint no encontrado"
    }), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "status": "error",
        "message": "Método no permitido"
    }), 405 