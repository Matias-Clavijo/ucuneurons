from flask import Blueprint, jsonify, request
import uuid
import base64
import json

from markdown_it.rules_inline import image

from app.models.gemini_model import gemini_model
from datetime import datetime

from app.services.ent_function import calcular_riesgo_inhalacion_ntp937

# Blueprint para el chatbot de evaluación de riesgos
risk_chatbot_bp = Blueprint('risk_chatbot', __name__)

# System instruction del experto en recopilación de datos
RISK_EXPERT_PROMPT = """
# ROL Y OBJETIVO
Eres un experto en evaluación de riesgos industriales y medioambientales con capacidad de análisis visual. Tu objetivo es analizar un conjunto de datos y una imagen sobre un proceso industrial para determinar la peligrosidad para los operarios y el medio ambiente. Tu respuesta debe ser únicamente un objeto JSON estructurado según el formato especificado, sin ningún texto, explicación o introducción adicional.

# PROCESO DE ANÁLISIS
Realizarás un análisis integral basado en toda la información proporcionada (texto e imagen).

## 1. Análisis de la Imagen del Entorno de Trabajo:
Primero, si esta presente, analiza la imagen proporcionada para identificar pistas visuales de riesgo. Busca específicamente:
- **EPP del Operario:** ¿Los trabajadores visibles usan casco, gafas, guantes, protección respiratoria? ¿El EPP parece adecuado o está ausente?
- **Estado del Entorno:** ¿Está el área ordenada y limpia o hay desorden, derrames, objetos en el suelo que puedan causar tropiezos?
- **Equipamiento de Seguridad:** ¿Se observan extintores, duchas de emergencia, lavaojos, sistemas de ventilación localizada (campanas de extracción)?
- **Condición de los Materiales:** ¿Los contenedores, mangueras o bombas parecen en buen estado, o se ven desgastados, corroídos o con fugas?
- **Señalización de Seguridad:** ¿Existen señales de advertencia de riesgos químicos, uso obligatorio de EPP, o rutas de evacuación?

## 2. Evaluación de Riesgo para Operarios:
Analiza los siguientes factores, **integrando los hallazgos del análisis de la imagen**, para determinar el nivel de riesgo ("LOW", "MID", "HIGH", "CRITICAL"):
- **Toxicidad y Peligrosidad de los Químicos:** ¿Son los químicos inherentemente peligrosos para la salud humana?
- **Naturaleza del Proceso:** ¿El proceso implica riesgo de salpicaduras, inhalación de vapores, contacto dérmico o esfuerzo físico?
- **Frecuencia y Duración:** Una alta frecuencia aumenta la exposición acumulada.
- **Entorno de Trabajo:** ¿Un espacio cerrado concentra vapores? ¿La falta de orden o de equipos de seguridad (visto en la imagen) aumenta el riesgo?
- **Materiales y Equipos:** ¿Los materiales son adecuados? ¿Su condición visible en la imagen presenta un riesgo?

## 3. Evaluación de Riesgo para el Medio Ambiente:
Analiza los siguientes factores, **integrando los hallazgos del análisis de la imagen**, para determinar el nivel de riesgo ("LOW", "MID", "HIGH", "CRITICAL"):
- **Ecotoxicidad de los Químicos:** ¿Son los químicos dañinos para la vida acuática, el suelo o el aire?
- **Potencial de Fuga o Derrame:** ¿El proceso o el estado del equipo (visto en la imagen) sugiere un alto riesgo de liberación al ambiente? ¿Existen sistemas de contención secundaria visibles?
- **Ubicación Geográfica (`place`):** ¿La cercanía a zonas sensibles (ríos, etc.) agrava un posible derrame?
- **Entorno Físico (`environment`):** Un proceso "Outdoor" tiene una ruta de liberación directa. Un proceso "Indoor" sin contención adecuada (visto en la imagen) puede llevar a una liberación a través de drenajes.

## 4. Determinación de Requisitos para el Operario (EPP):
Basado en el análisis completo (químicos, proceso, materiales e imagen), genera una lista de los elementos de protección personal **obligatorios** para realizar la tarea de forma segura. Infiere los requisitos estándar según las buenas prácticas de seguridad industrial para los riesgos identificados.
- **Ejemplos:** Para químicos volátiles, sugiere "Protección respiratoria con filtro para vapores orgánicos". Para riesgo de salpicaduras, "Gafas de seguridad antisalpicaduras y guantes de nitrilo". Para riesgo de caída de objetos, "Casco de seguridad".

# DATOS DE ENTRADA
Recibirás los datos en un formato multimodal: una imagen y un texto que describe la tarea a analizar.
- **Imagen:** Una fotografía del entorno de trabajo.
- **Texto:**
    - `chemicals`: Lista de productos químicos involucrados.
    - `place`: Ubicación de la planta o proceso.
    - `materials`: Equipos o materiales utilizados.
    - `frequency_of_use`: Con qué frecuencia se realiza la tarea.
    - `environment`: Si el proceso es en interiores o exteriores.
    - `process`: Descripción de la tarea que realiza el operario.
    - `additional_info`: Cualquier otra información relevante.

# FORMATO DE RESPUESTA OBLIGATORIO
Tu única salida debe ser un objeto JSON válido con la siguiente estructura. No incluyas `json` ni ````.

{
  "operators_risk_level": "LOW" | "MID" | "HIGH" | "CRITICAL",
  "environment_risk_level": "LOW" | "MID" | "HIGH" | "CRITICAL",
  "operators_risk_message": [
    "String explicando el primer factor de riesgo para el operario.",
    "String explicando el segundo factor de riesgo para el operario, posiblemente basado en la imagen."
  ],
  "environment_risk_message": [
    "String explicando el primer factor de riesgo para el medio ambiente.",
    "String explicando el segundo factor de riesgo para el medio ambiente, posiblemente basado en la imagen."
  ],
  "operator_requirements": [
    "Guantes de nitrilo resistentes a químicos",
    "Gafas de seguridad antisalpicaduras",
    "Protección respiratoria con filtro para vapores orgánicos",
    "Casco de seguridad"
  ]
}
"""

@risk_chatbot_bp.route('/')
def risk_chatbot_home():
    """Información del chatbot de evaluación de riesgos"""
    return jsonify({
        "message": "Chatbot Experto en Recopilación de Datos para Evaluación de Riesgos",
        "version": "1.0.0",
        "descripcion": "Asistente especializado en recopilar información sobre tareas industriales",
        "endpoints": [
            "POST /risk-chat/start - Iniciar nueva evaluación",
            "POST /risk-chat/<session_id>/message - Enviar mensaje",
            "POST /risk-chat/<session_id>/analyze-image - Analizar imagen del lugar de trabajo",
            "POST /risk-chat/<session_id>/submit-form - 🆕 ENVIAR CAMPOS + IMAGEN JUNTOS",
            "GET  /risk-chat/<session_id>/status - Ver estado de la recopilación",
            "GET  /risk-chat/<session_id>/history - Ver historial",
            "DELETE /risk-chat/<session_id> - Terminar evaluación"
        ],
        "objetivo": "Recopilar datos completos sobre tareas industriales para evaluación de riesgos"
    })

def start_risk_assessment():
    """Iniciar nueva sesión de evaluación de riesgos"""
    try:
        # Generar ID único para la sesión
        session_id = f"risk-{uuid.uuid4().hex[:8]}"
        
        result = gemini_model.create_chat_session(session_id, RISK_EXPERT_PROMPT)
        
        if result["status"] == "error":
            return {"result": result}

        welcome_result = gemini_model.send_chat_message(
            session_id, 
            "Hola, soy tu asistente para recopilar datos de evaluación de riesgos. Para comenzar, describe brevemente la tarea industrial que quieres evaluar."
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Sesión de evaluación de riesgos iniciada",
            "welcome_message": welcome_result.get("response", ""),
            "tipo": "risk_assessment",
            "timestamp": result["timestamp"]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@risk_chatbot_bp.route('/<session_id>/message', methods=['POST'])
def send_risk_message(session_id):
    """Enviar mensaje al chatbot de riesgos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        user_message = data.get("message", "")
        if not user_message:
            return jsonify({
                "status": "error",
                "message": "Message is required"
            }), 400
        
        # Enviar mensaje al modelo
        result = gemini_model.send_chat_message(session_id, user_message)
        
        if result["status"] == "error":
            return jsonify(result), 404 if "no encontrada" in result["message"] else 500
        
        # Verificar si la respuesta contiene JSON (evaluación completa)
        response_text = result["response"]
        is_complete = False
        
        try:
            import json
            if response_text.strip().startswith("{") and response_text.strip().endswith("}"):
                parsed_json = json.loads(response_text)
                if parsed_json.get("status") == "COMPLETO":
                    is_complete = True
        except:
            pass
        
        return jsonify({
            "status": "success",
            "response": response_text,
            "user_message": user_message,
            "session_id": session_id,
            "is_complete": is_complete,
            "timestamp": result["timestamp"]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@risk_chatbot_bp.route('/<session_id>/analyze-image', methods=['POST'])
def analyze_workplace_image(session_id):
    """Analizar imagen del lugar de trabajo para complementar la evaluación de riesgos"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        # Obtener imagen en base64
        image_base64 = data.get("image")
        user_context = data.get("context", "")
        
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
        
        # Prompt especializado para análisis de riesgos industriales con clasificación automática
        analysis_prompt = f"""Analiza esta imagen desde la perspectiva de SEGURIDAD INDUSTRIAL y EVALUACIÓN DE RIESGOS QUÍMICOS.

Contexto del usuario: {user_context}

PRIMERO, clasifica la imagen en una de estas categorías:
- "lugar_trabajo": Instalaciones, naves, áreas de trabajo
- "equipamiento_operadores": EPIs, equipos de protección, operadores
- "equipos_industriales": Maquinaria, sistemas de transferencia, contenedores
- "sistemas_seguridad": Duchas de emergencia, extintores, señalización
- "almacenamiento": Áreas de almacén, estanterías, contenedores de químicos
- "otros": Cualquier otra cosa relevante

SEGUNDO, proporciona un análisis detallado identificando:

1. **ENTORNO FÍSICO:**
   - Interior/exterior
   - Dimensiones aproximadas del espacio
   - Condiciones generales (limpieza, orden, etc.)

2. **SISTEMAS DE VENTILACIÓN:**
   - Ventilación natural (ventanas, aberturas)
   - Ventilación mecánica (extractores, sistemas HVAC)
   - Extracción localizada en puntos de trabajo

3. **EQUIPOS DE SEGURIDAD VISIBLES:**
   - Equipos de protección individual (EPIs)
   - Duchas de emergencia o lavaojos
   - Extintores o sistemas contra incendios
   - Señalización de seguridad

4. **ALMACENAMIENTO Y MANIPULACIÓN:**
   - Contenedores de químicos visibles
   - Sistemas de contención de derrames
   - Equipos de transferencia (bombas, mangueras)
   - Zonas de trabajo

5. **FACTORES DE RIESGO OBSERVABLES:**
   - Posibles fuentes de ignición
   - Áreas de confinamiento
   - Condiciones que podrían afectar la dispersión
   - Cualquier condición insegura visible

Estructura tu respuesta así:
CATEGORÍA: [categoría identificada]
DESCRIPCIÓN: [análisis detallado]

Sé específico y técnico en tu análisis. Si no puedes identificar algo claramente, indícalo."""
        
        # Analizar imagen con Gemini Vision
        analysis_result = gemini_model.analyze_image(image_data, analysis_prompt)
        
        if analysis_result["status"] == "error":
            return jsonify({
                "status": "error",
                "message": "Error al analizar la imagen",
                "details": analysis_result["message"]
            }), 500
        
        # Procesar el análisis para extraer categoría y descripción
        analysis_text = analysis_result['analysis']
        
        # Extraer categoría y descripción
        categoria = "otros"  # valor por defecto
        descripcion = analysis_text
        
        if "CATEGORÍA:" in analysis_text and "DESCRIPCIÓN:" in analysis_text:
            lines = analysis_text.split('\n')
            for line in lines:
                if line.startswith("CATEGORÍA:"):
                    categoria = line.replace("CATEGORÍA:", "").strip()
                elif line.startswith("DESCRIPCIÓN:"):
                    # Todo lo que viene después de DESCRIPCIÓN:
                    desc_index = analysis_text.find("DESCRIPCIÓN:")
                    descripcion = analysis_text[desc_index + len("DESCRIPCIÓN:"):].strip()
                    break
        
        # Crear metadata de la imagen
        imagen_metadata = {
            "tipo": categoria,
            "descripcion": descripcion,
            "timestamp": analysis_result["timestamp"]
        }
        
        # Enviar el análisis como mensaje del chatbot con contexto estructurado
        chat_message = f"""He analizado la imagen que enviaste. 

📸 **Tipo de imagen:** {categoria}

🔍 **Análisis detallado:**
{descripcion}

Esta información visual será incluida en el reporte final de evaluación de riesgos. Continuemos con la recopilación de datos restantes."""
        
        # Enviar mensaje con análisis a la sesión de chat
        chat_result = gemini_model.send_chat_message(session_id, chat_message)
        
        if chat_result["status"] == "error":
            return jsonify({
                "status": "error",
                "message": "Error al procesar análisis en el chat",
                "details": chat_result["message"]
            }), 500
        
        return jsonify({
            "status": "success",
            "image_analysis": {
                "raw_analysis": analysis_result["analysis"],
                "structured": imagen_metadata
            },
            "chat_response": chat_result["response"],
            "session_id": session_id,
            "timestamp": analysis_result["timestamp"]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@risk_chatbot_bp.route('/<session_id>/submit-form', methods=['POST'])
def submit_form_with_image(session_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        message = data.get("data", {})
        image_base64 = data.get("image")
        
        if not message:
            return jsonify({
                "status": "error",
                "message": "Se requiere al menos un mensaje o una imagen"
            }), 400
        
        results = []
        
        if message.strip():
            try:
                chat_result = gemini_model.send_chat_message(session_id, message)
                
                if chat_result["status"] == "error":
                    return jsonify({
                        "status": "error",
                        "message": "Error al procesar mensaje",
                        "details": chat_result["message"]
                    }), 500
                
                results.append({
                    "type": "message",
                    "status": "success",
                    "response": chat_result["response"]
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Error procesando mensaje: {str(e)}"
                }), 500
        
        # PASO 2: Procesar IMAGEN (si existe)
        if image_base64:
            try:
                # Decodificar imagen
                try:
                    image_data = base64.b64decode(image_base64)
                except Exception:
                    return jsonify({
                        "status": "error",
                        "message": "Datos de imagen en base64 inválidos"
                    }), 400
                
                # Prompt especializado para análisis de riesgos
                analysis_prompt = f"""Analiza esta imagen desde la perspectiva de SEGURIDAD INDUSTRIAL y EVALUACIÓN DE RIESGOS QUÍMICOS.

Contexto del usuario: {image_context}

PRIMERO, clasifica la imagen en una de estas categorías:
- "lugar_trabajo": Instalaciones, naves, áreas de trabajo
- "equipamiento_operadores": EPIs, equipos de protección, operadores
- "equipos_industriales": Maquinaria, sistemas de transferencia, contenedores
- "sistemas_seguridad": Duchas de emergencia, extintores, señalización
- "almacenamiento": Áreas de almacén, estanterías, contenedores de químicos
- "otros": Cualquier otra cosa relevante

SEGUNDO, proporciona un análisis detallado identificando:

1. **ENTORNO FÍSICO:**
   - Interior/exterior
   - Dimensiones aproximadas del espacio
   - Condiciones generales (limpieza, orden, etc.)

2. **SISTEMAS DE VENTILACIÓN:**
   - Ventilación natural (ventanas, aberturas)
   - Ventilación mecánica (extractores, sistemas HVAC)
   - Extracción localizada en puntos de trabajo

3. **EQUIPOS DE SEGURIDAD VISIBLES:**
   - Equipos de protección individual (EPIs)
   - Duchas de emergencia o lavaojos
   - Extintores o sistemas contra incendios
   - Señalización de seguridad

4. **ALMACENAMIENTO Y MANIPULACIÓN:**
   - Contenedores de químicos visibles
   - Sistemas de contención de derrames
   - Equipos de transferencia (bombas, mangueras)
   - Zonas de trabajo

5. **FACTORES DE RIESGO OBSERVABLES:**
   - Posibles fuentes de ignición
   - Áreas de confinamiento
   - Condiciones que podrían afectar la dispersión
   - Cualquier condición insegura visible

Estructura tu respuesta así:
CATEGORÍA: [categoría identificada]
DESCRIPCIÓN: [análisis detallado]

Sé específico y técnico en tu análisis. Si no puedes identificar algo claramente, indícalo."""
                
                # Analizar imagen con Gemini Vision
                analysis_result = gemini_model.analyze_image(image_data, analysis_prompt)
                
                if analysis_result["status"] == "error":
                    return jsonify({
                        "status": "error",
                        "message": "Error al analizar la imagen",
                        "details": analysis_result["message"]
                    }), 500
                
                # Procesar análisis estructurado
                analysis_text = analysis_result['analysis']
                categoria = "otros"
                descripcion = analysis_text
                
                if "CATEGORÍA:" in analysis_text and "DESCRIPCIÓN:" in analysis_text:
                    lines = analysis_text.split('\n')
                    for line in lines:
                        if line.startswith("CATEGORÍA:"):
                            categoria = line.replace("CATEGORÍA:", "").strip()
                        elif line.startswith("DESCRIPCIÓN:"):
                            desc_index = analysis_text.find("DESCRIPCIÓN:")
                            descripcion = analysis_text[desc_index + len("DESCRIPCIÓN:"):].strip()
                            break
                
                # Metadata de la imagen
                imagen_metadata = {
                    "tipo": categoria,
                    "descripcion": descripcion,
                    "timestamp": analysis_result["timestamp"]
                }
                
                # FUNCIONALIDAD IDÉNTICA AL ENDPOINT /analyze-image
                # Enviar el análisis como mensaje del chatbot con contexto estructurado
                chat_message = f"""He analizado la imagen que enviaste. 

📸 **Tipo de imagen:** {categoria}

🔍 **Análisis detallado:**
{descripcion}

Esta información visual será incluida en el reporte final de evaluación de riesgos. Continuemos con la recopilación de datos restantes."""
                
                # Enviar mensaje con análisis a la sesión de chat
                chat_result = gemini_model.send_chat_message(session_id, chat_message)
                
                if chat_result["status"] == "error":
                    return jsonify({
                        "status": "error",
                        "message": "Error al procesar análisis en el chat",
                        "details": chat_result["message"]
                    }), 500
                
                results.append({
                    "type": "image_analysis",
                    "status": "success",
                    "image_analysis": {
                        "raw_analysis": analysis_result["analysis"],
                        "structured": imagen_metadata
                    },
                    "chat_response": chat_result["response"]
                })
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "message": f"Error procesando imagen: {str(e)}"
                }), 500

        # RESPUESTA CONSOLIDADA
        # Determinar si la evaluación está completa (buscar en todas las respuestas)
        is_complete = False
        all_responses = []
        
        for result in results:
            if result["type"] == "message" and result.get("is_complete", False):
                is_complete = True
            
            if "response" in result:
                all_responses.append(result["response"])
            elif "chat_response" in result:
                all_responses.append(result["chat_response"])
        
        # También verificar si cualquier respuesta contiene JSON completo
        if not is_complete:
            for response in all_responses:
                try:
                    import json
                    if response.strip().startswith("{") and response.strip().endswith("}"):
                        parsed_json = json.loads(response)
                        if parsed_json.get("status") == "COMPLETO":
                            is_complete = True
                            break
                except:
                    continue
        
        chat_responses = all_responses
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "combined_response": "\n\n".join(chat_responses),
            "individual_results": results,
            "is_complete": is_complete,
            "processing_summary": {
                "message_processed": bool(message.strip()),
                "image_processed": bool(image_base64),
                "total_operations": len(results)
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@risk_chatbot_bp.route('/<session_id>/status', methods=['GET'])
def get_risk_status(session_id):
    """Obtener estado de la recopilación de datos"""
    try:
        # Obtener historial para analizar progreso
        history_result = gemini_model.get_chat_history(session_id)
        
        if history_result["status"] == "error":
            return jsonify(history_result), 404 if "no encontrada" in history_result["message"] else 500
        
        history = history_result["history"]
        
        # Analizar si hay JSON completo en las respuestas
        is_complete = False
        last_response = ""
        
        for msg in reversed(history):
            if msg["role"] == "model":
                last_response = msg["content"]
                try:
                    import json
                    if last_response.strip().startswith("{") and last_response.strip().endswith("}"):
                        parsed_json = json.loads(last_response)
                        if parsed_json.get("status") == "COMPLETO":
                            is_complete = True
                            break
                except:
                    continue
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "is_complete": is_complete,
            "total_messages": len(history),
            "last_response_preview": last_response[:200] + "..." if len(last_response) > 200 else last_response,
            "timestamp": history_result["timestamp"]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@risk_chatbot_bp.route('/<session_id>/history', methods=['GET'])
def get_risk_history(session_id):
    """Obtener historial completo de la evaluación"""
    try:
        result = gemini_model.get_chat_history(session_id)
        
        if result["status"] == "error":
            return jsonify(result), 404 if "no encontrada" in result["message"] else 500
        
        # Agregar información adicional sobre el tipo de sesión
        result["session_type"] = "risk_assessment"
        result["description"] = "Sesión de recopilación de datos para evaluación de riesgos"
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@risk_chatbot_bp.route('/<session_id>/analyze', methods=['POST'])
def analyze_v1(session_id):
    try:
        data = request.get_json()
        print(data)
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400


        message = data.get("data", {})
        image_base64 = message.get("image")

        if not message:
            return jsonify({
                "status": "error",
                "message": "Se requiere al menos un mensaje o una imagen"
            }), 400
        

        analysis_prompt = f"""
---
AQUÍ COMIENZA LA INFORMACIÓN PARA ANALIZAR:

[IMAGEN PROPORCIONADA en BASE64] = {image_base64}

- **chemicals:** {message.get("chemicals", "")}
- **place:** {message.get("place", "")}
- **materials:** {message.get("materials", "")}
- **frequency_of_use:** {message.get("frequency_of_use", "")}
- **environment:** {message.get("environment", "")}
- **process:** {message.get("process", "")}
- **additional_info:** {message.get("additional_info", "")}
        """
        print(analysis_prompt)

        try:
            chat_result = gemini_model.send_chat_message(session_id, analysis_prompt)

            if chat_result["status"] == "error":
                return jsonify({
                    "status": "error",
                    "message": "Error al procesar mensaje",
                    "chat_response": chat_result["message"].replace("```json ", "")
                }), 500

            chat_json_response = chat_result["response"].replace("```json", "").replace("```", "")

            json_result = json.loads(chat_json_response)
            print(f"🔍 JSON RESULT: {json_result}")
            return jsonify({
                "status": "success",
                "chat_response": json_result
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error procesando mensaje: {str(e)}"
            }), 500

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error procesando imagen: {str(e)}"
        }), 500

# Manejadores de errores específicos
@risk_chatbot_bp.errorhandler(404)
def risk_not_found(error):
    return jsonify({
        "status": "error",
        "message": "Sesión de evaluación de riesgos no encontrada"
    }), 404

@risk_chatbot_bp.errorhandler(405)
def risk_method_not_allowed(error):
    return jsonify({
        "status": "error",
        "message": "Método no permitido para este endpoint de evaluación de riesgos"
    }), 405 