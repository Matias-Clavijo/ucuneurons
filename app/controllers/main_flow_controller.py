from flask import Blueprint, jsonify, request
import requests
import json
import uuid
from datetime import datetime
from app.config.config import Config

# Blueprint para el flujo principal orquestador
main_flow_bp = Blueprint('main_flow', __name__)

# URL base para llamadas internas
INTERNAL_BASE_URL = f"http://127.0.0.1:{Config.API_PORT}"

@main_flow_bp.route('/evaluate-risk/')
def main_flow_home():
    """Información del orquestador principal"""
    return jsonify({
        "message": "Orquestador Principal de Evaluación de Riesgos",
        "version": "1.0.0",
        "description": "Sistema completo de evaluación de riesgos industriales",
        "endpoints": [
            "POST /evaluate-risk - Evaluación completa de riesgos",
            "GET  /evaluate-risk/<eval_id>/status - Estado de evaluación",
            "POST /evaluate-risk/interactive - Iniciar evaluación interactiva",
            "POST /evaluate-risk/<eval_id>/continue - Continuar evaluación interactiva"
        ],
        "modulos_integrados": [
            "✅ Módulo de Recopilación de Datos (Chatbot Experto)",
            "🔄 Módulo RAG (En integración)",
            "🔄 Módulo de Cálculo de Riesgos (En integración)",
            "🔄 Módulo de Reportes (En integración)"
        ]
    })

@main_flow_bp.route('/evaluate-risk', methods=['POST'])
def handle_full_risk_evaluation():
    """
    Endpoint principal para evaluación completa de riesgos
    Orquesta todo el flujo: Recopilación → RAG → Cálculo → Reporte
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        initial_prompt = data.get("prompt")
        if not initial_prompt:
            return jsonify({
                "status": "error",
                "message": "Prompt is required"
            }), 400
        
        eval_id = f"eval-{uuid.uuid4().hex[:8]}"
        
        # -------------------------------------------------------------------
        # PASO 1: RECOPILACIÓN DE DATOS (Módulo Chatbot Experto)
        # -------------------------------------------------------------------
        
        print(f"🚀 [{eval_id}] Iniciando evaluación completa...")
        print(f"📋 [{eval_id}] PASO 1: Recopilación de datos")
        
        # 1.1 Crear sesión de chatbot
        start_response = requests.post(f'{INTERNAL_BASE_URL}/risk-chat/start', json={
            "session_id": f"session-{eval_id}"
        })
        
        if start_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "Error al iniciar módulo de recopilación",
                "details": start_response.text
            }), 500
        
        session_data = start_response.json()
        session_id = session_data["session_id"]
        
        # 1.2 Enviar prompt inicial
        message_response = requests.post(
            f'{INTERNAL_BASE_URL}/risk-chat/{session_id}/message',
            json={"message": initial_prompt}
        )
        
        if message_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "Error en módulo de recopilación",
                "details": message_response.text
            }), 500
        
        chatbot_result = message_response.json()
        
        # 1.3 Verificar si necesita más información del usuario
        if not chatbot_result.get("is_complete"):
            return jsonify({
                "status": "pending_user_input",
                "eval_id": eval_id,
                "session_id": session_id,
                "next_question": chatbot_result.get("response"),
                "step": "data_collection",
                "progress": {
                    "current_step": 1,
                    "total_steps": 4,
                    "step_name": "Recopilación de Datos"
                }
            }), 202  # Accepted - Requiere más input
        
        # 1.4 Parsear JSON final del chatbot
        try:
            # El chatbot devuelve JSON como string en response
            datos_tarea_json = json.loads(chatbot_result["response"])
            if datos_tarea_json.get("status") != "COMPLETO":
                raise ValueError("Datos incompletos del chatbot")
            
            datos_tarea = datos_tarea_json["datos_tarea"]
            print(f"✅ [{eval_id}] PASO 1 COMPLETADO: Datos recopilados")
            
        except (json.JSONDecodeError, ValueError) as e:
            return jsonify({
                "status": "error",
                "message": "Error al procesar datos del chatbot",
                "details": str(e)
            }), 500
        
        # -------------------------------------------------------------------
        # PASO 2: ENRIQUECIMIENTO RAG (Módulo de tu compañero)
        # -------------------------------------------------------------------
        
        print(f"📚 [{eval_id}] PASO 2: Enriquecimiento con RAG")
        
        # Preparar datos para RAG
        quimicos = datos_tarea.get('quimicos_involucrados', [])
        pais = datos_tarea.get('contexto_fisico', {}).get('ubicacion_pais', 'España')
        
        # Llamar al módulo RAG (cuando esté implementado por tu compañero)
        rag_data = _call_rag_module(quimicos, pais, eval_id)
        
        if rag_data["status"] == "error":
            return jsonify({
                "status": "error",
                "message": "Error en módulo RAG",
                "details": rag_data.get("message")
            }), 500
        
        print(f"✅ [{eval_id}] PASO 2 COMPLETADO: Datos enriquecidos con RAG")
        
        # -------------------------------------------------------------------
        # PASO 3: CÁLCULO DE RIESGOS (Módulo de cálculo)
        # -------------------------------------------------------------------
        
        print(f"🧮 [{eval_id}] PASO 3: Cálculo de riesgos")
        
        # Llamar al motor de cálculo
        calculo_result = _call_calculation_engine(datos_tarea, rag_data["datos_enriquecidos"], eval_id)
        
        if calculo_result["status"] == "error":
            return jsonify({
                "status": "error",
                "message": "Error en módulo de cálculo",
                "details": calculo_result.get("message")
            }), 500
        
        print(f"✅ [{eval_id}] PASO 3 COMPLETADO: Riesgos calculados")
        
        # -------------------------------------------------------------------
        # PASO 4: REPORTE FINAL (Módulo de reportes)
        # -------------------------------------------------------------------
        
        print(f"📄 [{eval_id}] PASO 4: Generación de reporte")
        
        reporte_final = _generate_final_report(datos_tarea, rag_data["datos_enriquecidos"], calculo_result["resultado"], eval_id)
        
        print(f"🎉 [{eval_id}] EVALUACIÓN COMPLETA!")
        
        # -------------------------------------------------------------------
        # RESPUESTA FINAL
        # -------------------------------------------------------------------
        
        return jsonify({
            "status": "EVALUACION_COMPLETA",
            "eval_id": eval_id,
            "timestamp": datetime.now().isoformat(),
            "resultado_final": {
                "datos_recopilados": datos_tarea,
                "datos_enriquecidos": rag_data["datos_enriquecidos"],
                "calculo_riesgos": calculo_result["resultado"],
                "reporte": reporte_final
            },
            "metadatos": {
                "session_id": session_id,
                "tiempo_total": "calculado_en_implementacion_final",
                "modulos_ejecutados": ["chatbot", "rag", "calculo", "reporte"]
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "Error interno del orquestador",
            "details": str(e)
        }), 500

@main_flow_bp.route('/evaluate-risk/interactive', methods=['POST'])
def start_interactive_evaluation():
    """Iniciar evaluación interactiva (para frontend)"""
    try:
        data = request.get_json() or {}
        initial_prompt = data.get("prompt", "")
        
        eval_id = f"interactive-{uuid.uuid4().hex[:8]}"
        
        # Crear sesión de chatbot
        start_response = requests.post(f'{INTERNAL_BASE_URL}/risk-chat/start', json={
            "session_id": f"session-{eval_id}"
        })
        
        if start_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "Error al iniciar evaluación interactiva"
            }), 500
        
        session_data = start_response.json()
        session_id = session_data["session_id"]
        
        # Si hay prompt inicial, enviarlo
        if initial_prompt:
            message_response = requests.post(
                f'{INTERNAL_BASE_URL}/risk-chat/{session_id}/message',
                json={"message": initial_prompt}
            )
            
            if message_response.status_code == 200:
                chatbot_result = message_response.json()
                return jsonify({
                    "status": "interactive_started",
                    "eval_id": eval_id,
                    "session_id": session_id,
                    "response": chatbot_result.get("response"),
                    "is_complete": chatbot_result.get("is_complete", False)
                })
        
        return jsonify({
            "status": "interactive_started",
            "eval_id": eval_id,
            "session_id": session_id,
            "response": session_data.get("welcome_message", "")
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@main_flow_bp.route('/evaluate-risk/<eval_id>/continue', methods=['POST'])
def continue_interactive_evaluation(eval_id):
    """Continuar evaluación interactiva con respuesta del usuario"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        user_message = data.get("message")
        if not user_message:
            return jsonify({
                "status": "error",
                "message": "Message is required"
            }), 400
        
        # Derivar session_id del eval_id
        session_id = f"session-{eval_id}"
        
        # Enviar mensaje al chatbot
        message_response = requests.post(
            f'{INTERNAL_BASE_URL}/risk-chat/{session_id}/message',
            json={"message": user_message}
        )
        
        if message_response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": "Error al procesar mensaje"
            }), 500
        
        chatbot_result = message_response.json()
        
        # Si la recopilación está completa, ejecutar el resto del flujo
        if chatbot_result.get("is_complete"):
            return _execute_complete_flow_from_data(eval_id, session_id, chatbot_result["response"])
        
        return jsonify({
            "status": "interactive_continue",
            "eval_id": eval_id,
            "session_id": session_id,
            "response": chatbot_result.get("response"),
            "is_complete": False
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@main_flow_bp.route('/evaluate-risk/<eval_id>/status', methods=['GET'])
def get_evaluation_status(eval_id):
    """Obtener estado de una evaluación"""
    try:
        session_id = f"session-{eval_id}"
        
        # Consultar estado del chatbot
        status_response = requests.get(f'{INTERNAL_BASE_URL}/risk-chat/{session_id}/status')
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            return jsonify({
                "status": "success",
                "eval_id": eval_id,
                "chatbot_complete": status_data.get("is_complete", False),
                "total_messages": status_data.get("total_messages", 0),
                "current_step": "data_collection" if not status_data.get("is_complete") else "ready_for_rag"
            })
        else:
            return jsonify({
                "status": "not_found",
                "eval_id": eval_id,
                "message": "Evaluación no encontrada"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES PARA INTEGRACIÓN DE MÓDULOS
# -------------------------------------------------------------------

def _call_rag_module(quimicos, pais, eval_id):
    """Llamar al módulo RAG (placeholder para integración futura)"""
    try:
        # TODO: Reemplazar con llamada real al módulo RAG de tu compañero
        # rag_response = requests.post(f'{INTERNAL_BASE_URL}/rag/enrich', json={
        #     "quimicos": quimicos,
        #     "pais": pais
        # })
        
        # Por ahora, simulamos respuesta del RAG
        print(f"📚 [{eval_id}] Simulando módulo RAG para químicos: {quimicos}")
        
        return {
            "status": "success",
            "datos_enriquecidos": {
                "fds_encontradas": len(quimicos),
                "quimicos_data": {quimico: {"cas": "simulado", "peligros": ["simulado"]} for quimico in quimicos},
                "legislacion_pais": f"Normativa de {pais}",
                "notas": "Datos simulados - pendiente integración módulo RAG real"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en módulo RAG: {str(e)}"
        }

def _call_calculation_engine(datos_tarea, datos_enriquecidos, eval_id):
    """Llamar al motor de cálculo de riesgos (placeholder)"""
    try:
        # TODO: Reemplazar con llamada real al módulo de cálculo
        print(f"🧮 [{eval_id}] Simulando cálculo de riesgos")
        
        return {
            "status": "success",
            "resultado": {
                "nivel_riesgo": "MEDIO",
                "puntuacion": 65,
                "factores_criticos": ["Volatilidad", "Cantidad"],
                "recomendaciones": ["Mejorar ventilación", "EPIs requeridos"],
                "notas": "Cálculo simulado - pendiente integración motor real"
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error en módulo de cálculo: {str(e)}"
        }

def _generate_final_report(datos_tarea, datos_enriquecidos, resultado_calculo, eval_id):
    """Generar reporte final (placeholder)"""
    print(f"📄 [{eval_id}] Generando reporte final")
    
    return {
        "id_reporte": eval_id,
        "fecha_generacion": datetime.now().isoformat(),
        "resumen_ejecutivo": f"Evaluación de riesgo para {datos_tarea.get('quimicos_involucrados', [])}",
        "nivel_riesgo_final": resultado_calculo.get("nivel_riesgo", "NO_CALCULADO"),
        "acciones_recomendadas": resultado_calculo.get("recomendaciones", []),
        "url_reporte_pdf": f"/reports/{eval_id}.pdf",
        "notas": "Reporte simulado - pendiente integración módulo de reportes"
    }

def _execute_complete_flow_from_data(eval_id, session_id, chatbot_response):
    """Ejecutar flujo completo cuando el chatbot ha terminado"""
    try:
        # Parsear datos del chatbot
        datos_tarea_json = json.loads(chatbot_response)
        datos_tarea = datos_tarea_json["datos_tarea"]
        
        # Ejecutar RAG
        quimicos = datos_tarea.get('quimicos_involucrados', [])
        pais = datos_tarea.get('contexto_fisico', {}).get('ubicacion_pais', 'España')
        rag_data = _call_rag_module(quimicos, pais, eval_id)
        
        # Ejecutar cálculo
        calculo_result = _call_calculation_engine(datos_tarea, rag_data["datos_enriquecidos"], eval_id)
        
        # Generar reporte
        reporte_final = _generate_final_report(datos_tarea, rag_data["datos_enriquecidos"], calculo_result["resultado"], eval_id)
        
        return jsonify({
            "status": "EVALUACION_COMPLETA",
            "eval_id": eval_id,
            "resultado_final": {
                "datos_recopilados": datos_tarea,
                "datos_enriquecidos": rag_data["datos_enriquecidos"],
                "calculo_riesgos": calculo_result["resultado"],
                "reporte": reporte_final
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error en flujo completo: {str(e)}"
        }), 500 