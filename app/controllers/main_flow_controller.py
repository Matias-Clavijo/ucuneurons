
from flask import Blueprint, jsonify, request
import requests
import json
import uuid
from datetime import datetime
from app.config.config import Config

from app.controllers.risk_chatbot_controller import risk_chatbot_bp
from app.services.risk_enricher import risk_enricher

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
def evaluate_risk_complete():
    """
    FLUJO COMPLETO DE EVALUACIÓN DE RIESGO
    
    Paso 1: Chatbot → Paso 2: RAG → Paso 3: Cálculo → Paso 4: Reporte
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No se proporcionaron datos de entrada",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # PASO 1: Procesar con chatbot (si no viene ya procesado)
        if 'chatbot_result' not in data:
            return jsonify({
                "status": "error", 
                "message": "Se requiere resultado del chatbot. Usar endpoint /evaluate-risk/interactive primero.",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        chatbot_result = data['chatbot_result']
        
        # PASO 2: ENRIQUECIMIENTO CON MULTI-CONSULTA DIRIGIDA
        print("INICIANDO PASO 2: ENRIQUECIMIENTO CON MULTI-CONSULTA DIRIGIDA")
        enrichment_result = risk_enricher.enrich_task_data(chatbot_result)
        
        if enrichment_result.get("status") == "error":
            return jsonify({
                "status": "error",
                "message": f"Error en enriquecimiento: {enrichment_result.get('message')}",
                "paso_fallido": "Paso 2 - Enriquecimiento RAG",
                "timestamp": datetime.now().isoformat()
            }), 500
        
        # PASO 3: Cálculo de riesgo (TODO: Implementar cuando esté disponible)
        print("⚙️ PASO 3: CÁLCULO DE RIESGO (Pendiente implementación)")
        calculation_result = {
            "status": "pending",
            "message": "Módulo de cálculo de riesgo en desarrollo",
            "datos_para_calculo": enrichment_result["datos_enriquecidos"]
        }
        
        # PASO 4: Generación de reporte (TODO: Implementar cuando esté disponible)  
        print("📄 PASO 4: GENERACIÓN DE REPORTE (Pendiente implementación)")
        report_result = {
            "status": "pending",
            "message": "Módulo de generación de reportes en desarrollo"
        }
        
        # RESULTADO CONSOLIDADO
        return jsonify({
            "status": "success",
            "message": "Evaluación de riesgo completada exitosamente",
            "flujo_completo": {
                "paso_1_chatbot": {
                    "status": "completed",
                    "datos_recopilados": chatbot_result
                },
                "paso_2_enriquecimiento": {
                    "status": "completed", 
                    "strategy": "Multi-Consulta Dirigida",
                    "quimicos_procesados": enrichment_result.get("quimicos_procesados", []),
                    "objetivos_fds_buscados": len(risk_enricher.OBJETIVOS_DATOS_FDS),
                    "objetivos_legales_buscados": len(risk_enricher.OBJETIVOS_DATOS_LEGALES),
                    "datos_enriquecidos": enrichment_result["datos_enriquecidos"]
                },
                "paso_3_calculo": calculation_result,
                "paso_4_reporte": report_result
            },
            "timestamp": datetime.now().isoformat(),
            "processing_time_seconds": "TODO: Implementar medición de tiempo"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "paso_fallido": "Error general del orquestador",
            "timestamp": datetime.now().isoformat()
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

@main_flow_bp.route('/enrich-data', methods=['POST'])
def enrich_data_only():
    """
    ENDPOINT ESPECÍFICO PARA ENRIQUECIMIENTO DE DATOS
    
    Permite usar solo el Paso 2 (Multi-Consulta Dirigida) de forma independiente.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No se proporcionaron datos para enriquecer",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Validar que tenga la estructura esperada del chatbot
        if 'datos_tarea' not in data:
            return jsonify({
                "status": "error",
                "message": "Formato inválido. Se esperan datos_tarea del chatbot.",
                "formato_esperado": {
                    "datos_tarea": {
                        "quimicos_involucrados": ["quimico1", "quimico2"],
                        "contexto_fisico": {"ubicacion_pais": "España"}
                    }
                },
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Ejecutar enriquecimiento con Multi-Consulta Dirigida
        enrichment_result = risk_enricher.enrich_task_data(data)
        
        return jsonify(enrichment_result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "service": "RiskDataEnricher",
            "timestamp": datetime.now().isoformat()
        }), 500

@main_flow_bp.route('/enricher/status', methods=['GET'])
def get_enricher_status():
    """Estado del módulo de enriquecimiento"""
    return jsonify(risk_enricher.get_status())

@main_flow_bp.route('/enricher/objectives', methods=['GET'])
def get_enricher_objectives():
    """Obtener los objetivos de búsqueda configurados"""
    return jsonify({
        "objetivos_fds": risk_enricher.OBJETIVOS_DATOS_FDS,
        "objetivos_legales": risk_enricher.OBJETIVOS_DATOS_LEGALES,
        "total_objetivos_fds": len(risk_enricher.OBJETIVOS_DATOS_FDS),
        "total_objetivos_legales": len(risk_enricher.OBJETIVOS_DATOS_LEGALES),
        "estrategia": "Multi-Consulta Dirigida",
        "descripcion": "Busca específicamente cada objetivo para cada químico de forma exhaustiva"
    })

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