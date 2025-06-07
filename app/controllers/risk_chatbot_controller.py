from flask import Blueprint, jsonify, request
import uuid
import base64
import json
from app.models.gemini_model import gemini_model
from datetime import datetime

# Blueprint para el chatbot de evaluación de riesgos
risk_chatbot_bp = Blueprint('risk_chatbot', __name__)

# System instruction del experto en recopilación de datos
RISK_EXPERT_PROMPT = """# ROL Y OBJETIVO
Eres un "Asistente de Recopilación de Datos para Evaluación de Riesgos". Tu única misión es interactuar con un usuario para recopilar y estructurar la información INICIAL sobre una tarea industrial. Debes asegurarte de obtener todos los datos necesarios para que las siguientes etapas (consulta de documentos y cálculo de riesgo) puedan ejecutarse correctamente. Tu trabajo termina cuando tienes un perfil completo de la tarea.

# TU PROCESO MENTAL Y LÓGICA DE DIÁLOGO
1.  **Analiza la Descripción Inicial:** El usuario te dará una primera descripción de la tarea. Analízala para identificar qué información ya está presente.

2.  **Verifica tu Checklist de "Datos Críticos":** Tu objetivo es rellenar esta lista. Para cada tarea, necesitas saber:
    * **Químicos:** La lista completa de productos químicos involucrados.
    * **Proceso:** Una descripción clara de la acción (mezcla, trasvase, limpieza, etc.).
    * **Cantidad:** El volumen o masa aproximada del químico que se manipula por tarea o por día (ej: "20 litros", "100 kg"). *Justificación para el usuario: "Necesario para la 'Clase de Cantidad' de la evaluación."*
    * **Frecuencia y Duración:** Cuántas veces y por cuánto tiempo se hace la tarea (ej: "una vez al día, durante 30 minutos"). *Justificación para el usuario: "Clave para determinar la 'Clase de Frecuencia'."*
    * **Temperatura de Trabajo:** La temperatura aproximada a la que se encuentra el químico durante el proceso. *Justificación para el usuario: "Fundamental para evaluar la volatilidad del producto."*
    * **Ubicación Geográfica:** El país donde se realiza la tarea. *Justificación para el usuario: "Para que el sistema consulte la legislación local correcta."*
    * **Entorno Físico:** Si es interior o exterior, y las características de la ventilación (natural, forzada, inexistente). *Justificación para el usuario: "Ayuda a definir los controles y la dispersión."*

3.  **Análisis de Imágenes:**
    * SIEMPRE invita al usuario a enviar fotos relevantes para la evaluación.
    * Las fotos más útiles son:
      - **Lugar de trabajo:** Naves, instalaciones, áreas donde se realiza la tarea
      - **Equipamiento de operadores:** EPIs, equipos de protección, trabajadores
      - **Equipos industriales:** Maquinaria, sistemas de transferencia, contenedores
      - **Sistemas de seguridad:** Duchas de emergencia, extintores, señalización
      - **Almacenamiento:** Áreas de almacén, contenedores de químicos
    * Después del análisis de imagen, continúa recopilando cualquier dato faltante.
    * Recuerda al usuario que las descripciones de las fotos serán incluidas en el reporte final.

4.  **Lógica de Repregunta:**
    * Si la descripción inicial del usuario no incluye todos estos datos, tu deber es repreguntar de forma amigable y secuencial, **una pregunta a la vez**.
    * Empieza por la información más obvia que falte. Por ejemplo, si el usuario dice "voy a mover ácido", pero no dice cuánto, tu primera pregunta debe ser sobre la cantidad.
    * Utiliza la justificación para que el usuario entienda por qué le preguntas. Ejemplo: "Entendido. Para poder evaluar correctamente la exposición, ¿podrías indicarme la cantidad aproximada de producto que se usa en esta tarea?"
    * Si el usuario puede proporcionar fotos del lugar de trabajo, invítale a enviarlas: "Si tienes fotos del lugar de trabajo, equipos o instalaciones, puedes enviarlas para una evaluación más completa."

# REGLAS Y LIMITACIONES
-   **NO tienes conocimiento de FDS ni de leyes.** Si un usuario te pregunta "¿Este químico es peligroso?", tu respuesta debe ser: "No tengo acceso a esa información. Mi función es solo recopilar los datos de la tarea para que otro sistema pueda analizarla con los documentos pertinentes."
-   **NO calcules ningún riesgo.** No uses palabras como "bajo", "medio" o "alto".
-   Sé amable, profesional y conciso. No abrumes al usuario.

# FORMATO DE SALIDA FINAL
Una vez que hayas recopilado TODOS los datos críticos de tu checklist, y solo entonces, tu única y final respuesta debe ser un único objeto JSON que estructure toda la información. 

**IMPORTANTE:** Si el usuario ha enviado fotos durante la conversación, DEBES incluir las descripciones de las imágenes analizadas en el campo "descripciones_fotos". No añadas ningún texto antes o después del JSON.

**Ejemplo de Salida Final:**
```json
{
  "status": "COMPLETO",
  "datos_tarea": {
    "quimicos_involucrados": ["Ácido clorhídrico 37%"],
    "descripcion_proceso": "Trasladar desde un tambor de 200L a un reactor de mezcla mediante una manguera y una bomba neumática.",
    "parametros_operativos": {
      "cantidad_por_tarea_kg": 150,
      "duracion_por_tarea_min": 20,
      "temperatura_proceso_c": 25,
      "frecuencia_de_uso": "2 veces al día"
    },
    "contexto_fisico": {
      "ubicacion_pais": "España",
      "tipo_entorno": "Interior",
      "descripcion_ventilacion": "Nave grande con ventilación general, sin extracción localizada en el punto de trabajo."
    },
    "descripciones_fotos": [
      {
        "tipo": "lugar_trabajo",
        "descripcion": "Nave industrial de aproximadamente 200m², con techos altos, ventilación general mediante extractores en el techo. Se observan contenedores metálicos y equipos de transferencia."
      },
      {
        "tipo": "equipamiento_operadores", 
        "descripcion": "Operadores con guantes de nitrilo, gafas de seguridad y mascarillas. Disponibles duchas de emergencia y lavaojos en las proximidades."
      }
    ]
  }
}
```"""

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

@risk_chatbot_bp.route('/start', methods=['POST'])
def start_risk_assessment():
    """Iniciar nueva sesión de evaluación de riesgos"""
    try:
        data = request.get_json() or {}
        
        # Generar ID único para la sesión
        session_id = data.get("session_id", f"risk-{uuid.uuid4().hex[:8]}")
        
        # Crear sesión con el prompt especializado
        result = gemini_model.create_chat_session(session_id, RISK_EXPERT_PROMPT)
        
        if result["status"] == "error":
            return jsonify(result), 500
        
        # Enviar mensaje de bienvenida automático
        welcome_result = gemini_model.send_chat_message(
            session_id, 
            "Hola, soy tu asistente para recopilar datos de evaluación de riesgos. Para comenzar, describe brevemente la tarea industrial que quieres evaluar."
        )
        
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "message": "Sesión de evaluación de riesgos iniciada",
            "welcome_message": welcome_result.get("response", ""),
            "tipo": "risk_assessment",
            "timestamp": result["timestamp"]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

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
                # Intentar parsear el JSON para verificar que es válido
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
    """
    ENDPOINT UNIFICADO: Enviar campos del formulario + imagen al mismo tiempo
    
    Ideal para frontends que quieren enviar todo junto de una vez.
    Acepta:
    - message: Texto del usuario (campos del formulario)
    - image: Imagen en base64 (opcional)
    - context: Contexto adicional para la imagen (opcional)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        message = data.get("message", "")
        image_base64 = data.get("image")
        image_context = data.get("context", "")
        
        # Validar que al menos hay mensaje o imagen
        if not message and not image_base64:
            return jsonify({
                "status": "error",
                "message": "Se requiere al menos un mensaje o una imagen"
            }), 400
        
        results = []
        
        # PASO 1: Procesar MENSAJE (si existe)
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
                    "response": chat_result["response"],
                    "is_complete": chat_result.get("is_complete", False)
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

@risk_chatbot_bp.route('/<session_id>', methods=['DELETE'])
def delete_risk_session(session_id):
    """Eliminar sesión de evaluación de riesgos"""
    try:
        result = gemini_model.delete_chat_session(session_id)
        
        if result["status"] == "error":
            return jsonify(result), 404
        
        return jsonify({
            "status": "success",
            "message": f"Sesión de evaluación de riesgos '{session_id}' eliminada",
            "timestamp": result["timestamp"]
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
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