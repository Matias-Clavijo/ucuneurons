import os
import tempfile
import logging
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from app.models.rag_faiss_model import rag_faiss_model


logger = logging.getLogger(__name__)

# Crear Blueprint para RAG FAISS endpoints
rag_faiss_bp = Blueprint("rag_faiss", __name__)

# Configuración de archivos permitidos
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file):
    """Validar el tamaño del archivo"""
    if hasattr(file, "content_length") and file.content_length:
        return file.content_length <= MAX_FILE_SIZE
    return True


@rag_faiss_bp.route("/")
def rag_faiss_home():
    """Información de los endpoints RAG FAISS disponibles"""
    return jsonify(
        {
            "message": "Endpoints RAG FAISS disponibles",
            "version": "1.0.0",
            "engine": "FAISS + LangChain + Google Generative AI",
            "endpoints": [
                "POST /api/rag-faiss/ingest - Ingestar documentos",
                "POST /api/rag-faiss/query - Consulta con RAG",
                "POST /api/rag-faiss/search - Búsqueda de documentos",
                "GET  /api/rag-faiss/stats - Estadísticas del sistema",
                "GET  /api/rag-faiss/health - Estado del sistema",
            ],
            "supported_formats": list(ALLOWED_EXTENSIONS),
            "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        }
    )


@rag_faiss_bp.route("/ingest", methods=["POST"])
def ingest_documents():
    """Ingestar documentos en el sistema FAISS"""
    try:
        # Verificar si se enviaron archivos
        if "files" not in request.files:
            return (
                jsonify(
                    {"status": "error", "message": "No se proporcionaron archivos"}
                ),
                400,
            )

        files = request.files.getlist("files")

        if not files or all(file.filename == "" for file in files):
            return (
                jsonify({"status": "error", "message": "No se seleccionaron archivos"}),
                400,
            )

        # Metadatos adicionales
        metadata = {}

        # Metadatos básicos
        form_metadata_fields = [
            "title",
            "author",
            "category",
            "document_type",
            "language",
            "version",
            "creation_date",
            "expiry_date",
            "department",
            "classification",
            "chemical_names",
            "safety_level",
            "regulatory_compliance",
            "facility",
            "process_area",
        ]

        for field in form_metadata_fields:
            if request.form.get(field):
                metadata[field] = request.form.get(field)

        # Procesar archivos
        temp_files = []
        file_paths = []

        try:
            for file in files:
                if file.filename == "":
                    continue

                # Verificar extensión del archivo
                if not allowed_file(file.filename):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"Tipo de archivo no permitido: {file.filename}. Formatos soportados: {', '.join(ALLOWED_EXTENSIONS)}",
                            }
                        ),
                        400,
                    )

                # Verificar tamaño del archivo
                if not validate_file_size(file):
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": f"El archivo {file.filename} excede el tamaño máximo de {MAX_FILE_SIZE // (1024 * 1024)}MB",
                            }
                        ),
                        400,
                    )

                # Guardar archivo temporal
                filename = secure_filename(file.filename)
                temp_dir = tempfile.mkdtemp()
                temp_path = os.path.join(temp_dir, filename)

                file.save(temp_path)
                temp_files.append((temp_path, temp_dir))
                file_paths.append(temp_path)

            if not file_paths:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "No se procesaron archivos válidos",
                        }
                    ),
                    400,
                )

            # Procesar documentos con el modelo FAISS
            result = rag_faiss_model.process_documents(file_paths, metadata)

            return jsonify(result)

        finally:
            # Limpiar archivos temporales
            for temp_path, temp_dir in temp_files:
                try:
                    os.remove(temp_path)
                    os.rmdir(temp_dir)
                except OSError:
                    pass

    except Exception as e:
        logger.error(f"Error en ingestión de documentos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_faiss_bp.route("/query", methods=["POST"])
def query_documents():
    """Realizar consulta RAG"""
    try:
        request_data = request.get_json()
        if not request_data:
            return (
                jsonify({"status": "error", "message": "No se proporcionaron datos"}),
                400,
            )

        question = request_data.get("question", "")
        if not question:
            return (
                jsonify(
                    {"status": "error", "message": "La pregunta no puede estar vacía"}
                ),
                400,
            )

        k = request_data.get("k", 4)  # Número de documentos a recuperar

        result = rag_faiss_model.answer_question(question, k=k)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error en consulta RAG: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_faiss_bp.route("/search", methods=["POST"])
def search_documents():
    """Buscar documentos similares"""
    try:
        request_data = request.get_json()
        if not request_data:
            return (
                jsonify({"status": "error", "message": "No se proporcionaron datos"}),
                400,
            )

        query = request_data.get("query", "")
        if not query:
            return (
                jsonify(
                    {"status": "error", "message": "La consulta no puede estar vacía"}
                ),
                400,
            )

        k = request_data.get("k", 4)

        try:
            docs = rag_faiss_model.search_documents(query, k=k)

            # Formatear resultados
            results = []
            for doc in docs:
                result_item = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Desconocido"),
                    "document_id": doc.metadata.get("document_id", ""),
                    "chunk_index": doc.metadata.get("chunk_index", 0),
                }
                results.append(result_item)

            return jsonify(
                {
                    "status": "success",
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "searched_at": rag_faiss_model.documents_metadata,
                }
            )

        except ValueError as e:
            return jsonify({"status": "error", "message": str(e)}), 400

    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_faiss_bp.route("/stats", methods=["GET"])
def get_stats():
    """Obtener estadísticas del sistema RAG FAISS"""
    try:
        stats = rag_faiss_model.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_faiss_bp.route("/health", methods=["GET"])
def health_check():
    """Verificar estado del sistema"""
    try:
        stats = rag_faiss_model.get_stats()

        health_status = {
            "status": "healthy" if stats["status"] == "success" else "unhealthy",
            "timestamp": stats.get("retrieved_at", ""),
            "vector_store_exists": stats.get("vector_store_exists", False),
            "total_documents": stats.get("total_documents", 0),
            "total_chunks": stats.get("total_chunks", 0),
            "embedding_model": stats.get("embedding_model", ""),
            "chat_model": stats.get("chat_model", ""),
        }

        return jsonify(health_status)

    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@rag_faiss_bp.route("/analyze-multi-field", methods=["POST"])
def analyze_multi_field():
    """Analizar prompt maestra y extraer 4 campos específicos con múltiples requests"""
    try:
        request_data = request.get_json()
        if not request_data:
            return (
                jsonify({"status": "error", "message": "No se proporcionaron datos"}),
                400,
            )

        # PROMPT MAESTRA (con placeholders)
        master_prompt_template = """PROMPT maestra
------
PROMPT maestra
------
Clasificacion de procedimientos:

Tu misión es analizar un escenario de trabajo y clasificar el procedimiento según los criterios técnicos que se proporcionan a continuación. Debes basar tu análisis *estrictamente* en la información contenida dentro de este prompt.
*[CONTEXTO DE REFERENCIA]*
*Sección A: Criterios de Clasificación de Procedimientos (NTP 937)*
•⁠  ⁠*Determinación del Procedimiento de Trabajo:* Este paso evalúa cómo el procedimiento de utilización del agente químico afecta a su liberación al ambiente. Se asigna una clase y una puntuación según el nivel de contención del proceso.
•⁠  ⁠*Clase 4: Dispersivo*
  * Descripción: Procesos que por su naturaleza tienden a esparcir el agente químico.
  * Ejemplos: Pintura a pistola, taladro, muela, vaciado de sacos a mano, de cubos..., Soldadura al arco..., Limpieza con trapos, Máquinas portátiles (sierras, cepillos...).
  * Puntuación de procedimiento: 1
•⁠  ⁠*Clase 3: Abierto*
  * Descripción: El producto está expuesto al ambiente pero el proceso no está diseñado para dispersarlo activamente.
  * Ejemplos: Conductos del reactor, mezcladores abiertos, pintura a brocha, a pincel, puesto de acondicionamiento (toneles, bidones...), Manejo y vigilancia de máquinas de impresión...
  * Puntuación de procedimiento: 0,5
•⁠  ⁠*Clase 2: Cerrado / abierto regularmente*
  * Descripción: El proceso está contenido, pero se abre de forma regular para realizar tareas.
  * Ejemplos: Reactor cerrado con cargas regulares de agentes químicos, toma de muestras, máquina de desengrasar en fase líquida o de vapor...
  * Puntuación de procedimiento: 0,05
•⁠  ⁠*Clase 1: Cerrado permanente*
  * Descripción: El proceso está completamente aislado del ambiente de trabajo.
  * Ejemplos: Reactor químico.
  * Puntuación de procedimiento: 0,001
Neceito que me devuelvas una clase del 1 al 4, en base a esta informacion dada.

---------
Clasifiacion de proteccion
Actúa como un Higienista Industrial en una planta quimica. Tu misión es evaluar las medidas de protección colectiva de un escenario de trabajo y clasificarlo según los 5 niveles de protección definidos en el contexto técnico que se proporciona a continuación. Debes basar tu análisis *estrictamente* en la información contenida dentro de este prompt y no utilizar ningún conocimiento externo.
*[CONTEXTO DE REFERENCIA: Criterios de Clasificación de la Protección Colectiva]*
•⁠  ⁠*Clase 5 (Puntuación: 10)*
  * *Ejemplos:* "Trabajo en espacio con aberturas limitadas de entrada y salida y ventilación natural desfavorable".
  * *Palabras Clave:* Espacio confinado, tanque, depósito, alcantarilla, sin ventilación, ventilación natural desfavorable.
•⁠  ⁠*Clase 4 (Puntuación: 1)*
  * *Ejemplos:* "Ausencia de ventilación mecánica".
  * *Palabras Clave:* Ventilación natural, sin ventilación mecánica, ventanas abiertas.
•⁠  ⁠*Clase 3 (Puntuación: 0,7)*
  * *Ejemplos:* "Trabajos en intemperie", "Trabajador alejado de la fuente de emisión", "Ventilación mecánica general".
  * *Palabras Clave:* Intemperie, exterior, al aire libre, ventilación general, dilución, trabajador lejos.
•⁠  ⁠*Clase 2 (Puntuación: 0,1)*
  * *Ejemplos:* "Campana superior", "Rendija de aspiración", "Mesa con aspiración", "Aspiración integrada a la herramienta", "Cabina de pequeñas dimensiones ventilada", "Cabina horizontal", "Cabina vertical".
  * *Palabras Clave:* Extracción localizada, campana, brazo de extracción, mesa aspirante, aspiración en herramienta.
•⁠  ⁠*Clase 1 (Puntuación: 0,001)*
  * *Ejemplos:* "Captación envolvente (vitrina de laboratorio)".
  * *Palabras Clave:* Vitrina, campana de gases, captación envolvente, sistema cerrado, contención total.

Debes basar tu análisis *estrictamente* en la información contenida dentro de este prompt, y retornar un numero del 1 al 5 en base a la clase mas adecuada para el quimico.
-----------
VLA
¡Entendido! Quieres un prompt con una estructura similar al que mostraste, pero adaptado para que el modelo determine el Factor de Corrección (FC_VLA) basándose en la tabla que adjuntaste y en la lógica de que tu RAG podría proporcionar múltiples valores de VLA.

Aquí tienes una propuesta de prompt que sigue esa estructura y lógica:

Prompt para Determinar el Factor de Corrección (FC_VLA)
Tu misión:
Tu misión es determinar el Factor de Corrección (FC_VLA) correcto basándote en el/los Valor(es) Límite Ambiental(es) (VLA) proporcionados. Debes basar tu análisis estrictamente en las reglas y criterios definidos a continuación.

*[CONTEXTO DE REFERENCIA]*

Sección A: Regla de Selección del VLA de Referencia

Recepción de Datos: Se te proporcionará uno o más valores de VLA extraídos de Fichas de Datos de Seguridad. Estos valores estarán en mg/m³.
Selección del Valor más Restrictivo: Si recibes múltiples valores de VLA, debes seleccionar el valor numérico más bajo. Este valor será el "VLA de referencia" que utilizarás para la clasificación en la Sección B. Esta regla se basa en el principio de precaución, utilizando siempre el escenario más desfavorable.
Sección B: Criterios de Asignación del Factor de Corrección (FC_VLA) - Basado en Tabla 11 NTP 937

Una vez determinado el "VLA de referencia" según la Sección A, asígnale el FC_VLA correspondiente usando las siguientes clases:

Clase 1: FC_VLA = 1

Condición: Si el VLA de referencia es mayor que 0,1.
(VLA 
ref
​
 >0,1)
Clase 2: FC_VLA = 10

Condición: Si el VLA de referencia es mayor que 0,01 y menor o igual a 0,1.
(0,01<VLA 
ref
​
 ≤0,1)
Clase 3: FC_VLA = 30

Condición: Si el VLA de referencia es mayor que 0,001 y menor o igual a 0,01.
(0,001<VLA 
ref
​
 ≤0,01)
Clase 4: FC_VLA = 100

Condición: Si el VLA de referencia es menor o igual a 0,001.
(VLA 
ref
​
 ≤0,001)
*[FIN DEL CONTEXTO DE REFERENCIA]*

Instrucción final:
Analiza el/los VLA proporcionados, aplica las reglas de las Secciones A y B, y devuelve únicamente el valor numérico final del FC_VLA que corresponda.

---------
Frases H
Actúa como un Analista de Riesgos Químicos. Tu objetivo es analizar un producto químico específico para identificar sus peligros y realizar una clasificación preliminar. Tu respuesta debe basarse en dos fuentes:
1 La Ficha de Datos de Seguridad (FDS) del químico, la cual debes consultar.
2 El contexto de referencia sobre clasificación de peligros que se proporciona a continuación.

⠀*[CONTEXTO DE REFERENCIA: Tabla de Clasificación de Peligro (NTP 937)]*
| *Clase de Peligro* | *Frases H* |
|---|---|
| *1* | Tiene frases H, pero no tiene ninguna de las que aparecen a continuación |
| *2* | H335, H336 |
| *3* | H304, H332, H361, H361d, H361f, H361fd, H362, H371, H373, EUH071 |
| *4* | H331, H334, H341, H351, H360, H360F, H360FD, H360D, H360Df, H360Fd, H370, H372, EUH029, EUH031 |
| *5* | H330, H340, H350, H350i, EUH032, EUH070 |
Export to Sheets
*[QUÍMICO A ANALIZAR]* [Aquí el usuario insertará el nombre del químico, por ejemplo: "Estireno"]
*[TAREA A REALIZAR]* Realiza el siguiente análisis en dos partes, de forma clara y estructurada:
*Parte 1: Extracción Exhaustiva de Peligros (Fuente: FDS)*
1 Consulta la FDS del químico indicado en la entrada.
2 Extrae y presenta en un listado todas las Frases de Peligro (Frases H) que figuran en la Sección 2 de su FDS, incluyendo el código pero no descripción completa.

---------

Volatilidad o pulverulencia


### MISIÓN Y ROL ###
Eres un Experto en Higiene Industrial y Prevención de Riesgos Laborales, especializado en la interpretación de Fichas de Datos de Seguridad (FDS) según la normativa NTP 937 de España. Tu misión es analizar el contexto extraído de una FDS y, siguiendo un riguroso proceso lógico, determinar la "Puntuación de volatilidad o pulverulencia". Actúa con precisión, basándote únicamente en los datos proporcionados.

### REGLA GENERAL DE PRECAUCIÓN (MÁS IMPORTANTE) ###
En cualquier paso del proceso, si encuentras información ambigua, contradictoria o una **falta crítica de datos** que impide una clasificación clara y definitiva, DEBES aplicar el principio de precaución: **asigna inmediatamente la clase más desfavorable (Clase 3) y su puntuación correspondiente (100)**. Indica en tu razonamiento por qué aplicaste esta regla.

### CONTEXTO ###
{aqui_insertas_los_10-15_chunks_de_la_FDS}
Temperatura de Trabajo Proporcionada: {aqui_insertas_la_temperatura_de_trabajo_o_No_proporcionada}

### PROCESO DE DECISIÓN OBLIGATORIO (PENSAR PASO A PASO) ###
Para llegar al resultado final, DEBES seguir estos pasos en orden estricto, siempre respetando la Regla General de Precaución.

**Paso 1: Análisis del Estado Físico.**
Primero, examina todo el contexto para identificar el estado físico del producto. Las claves son "Estado físico", "apariencia", "descripción". Clasifícalo como "Sólido", "Líquido" o "Gas". Si el estado físico no se puede determinar con certeza, aplica la Regla General de Precaución.

**Paso 2: Aplicación de Reglas por Caso.**
Basado en el estado físico, aplica UNO de los siguientes casos:

* **CASO A: Gas o Proceso de Pulverización (Spraying)**
    * **Condición:** Si el estado es "Gas", se describe como "humo", o el contexto menciona un proceso de "pulverización" o "spraying".
    * **Acción:** La "Clase Intermedia" es **3**. Ve directamente al Paso 4.

* **CASO B: Sólido (Análisis de Pulverulencia)**
    * **Condición:** Si el estado es "Sólido".
    * **Acción:** Analiza la descripción física del material (ej: "polvo fino", "granulado").
        * Si la descripción encaja claramente en una clase, asígnala según la Tabla 7:
            * **Clase 3:** Polvo fino que queda en suspensión.
            * **Clase 2:** Polvo en grano que sedimenta rápido.
            * **Clase 1:** Pastillas, granulado, escamas sin apenas emisión.
        * Si la descripción es ambigua o demasiado genérica (ej: "sólido blanco"), aplica la **Regla General de Precaución** y asigna la **Clase 3**.

* **CASO C: Líquido (Análisis de Volatilidad)**
    * **Condición:** Si el estado es "Líquido".
    * **Acción:** Revisa si dispones del "Punto de Ebullición (°C)" y la "Temperatura de Trabajo (°C)".
        * Si ambos datos están disponibles y son numéricos, usa la Figura 2 para determinar la "Clase Intermedia" (1-BAJA, 2-MEDIA, 3-ALTA). Si el punto cae en una línea, elige la clase superior.
        * Si el "Punto de Ebullición" es "no determinado" o no se encuentra, O si la "Temperatura de Trabajo" es "No proporcionada", aplica la **Regla General de Precaución** y asigna directamente la **Clase 3**.

**Paso 3: Determinación de la Clase Intermedia.**
Registra la "Clase Intermedia" (1, 2 o 3) que determinaste en el Paso 2.

**Paso 4: Cálculo de la Puntuación Final.**
Convierte la "Clase Intermedia" en la "Puntuación Final" usando la Tabla 10:
* Si Clase = 3 -> **Puntuación = 100**
* Si Clase = 2 -> **Puntuación = 10**
* Si Clase = 1 -> **Puntuación = 1**

### FORMATO DE OUTPUT OBLIGATORIO ###
Debes devolver tu análisis en un único bloque de código JSON, sin explicaciones adicionales fuera del JSON. La estructura debe ser la siguiente:

```json
{
  "razonamiento": [
    "Paso 1: [Aquí describes cómo identificaste el estado físico y cuál fue, o si fue incierto]",
    "Paso 2: [Aquí describes qué caso (A, B, o C) aplicaste. Si aplicaste la Regla de Precaución, explica exactamente por qué (ej: 'Punto de ebullición no determinado')]",
    "Paso 3: [Aquí indicas la Clase Intermedia resultante]",
    "Paso 4: [Aquí indicas cómo convertiste la clase en la puntuación final]"
  ],
  "estado_fisico_identificado": "Sólido / Líquido / Gas / Incierto",
  "caso_aplicado": "CASO A: Gas/Pulverización / CASO B: Sólido / CASO C: Líquido / Regla General de Precaución",
  "clase_intermedia": "1 / 2 / 3",
  "datos_faltantes": "[Lista aquí cualquier dato crucial que no se encontró y que forzó el uso de la regla de precaución]",
  "puntuacion_final": "1 / 10 / 100"
}

"""
        if not master_prompt_template:
            return (
                jsonify(
                    {"status": "error", "message": "El prompt maestra no puede estar vacío"}
                ),
                400,
            )

        # Variables dinámicas para reemplazar en la prompt
        chemical_name = request_data.get("chemical_name", "")
        temperature = request_data.get("temperature", "No proporcionada")
        
        # PROCESAR PROMPT MAESTRA: Reemplazar placeholders con datos reales
        master_prompt = _process_master_prompt_with_chunks(
            master_prompt_template, 
            chemical_name, 
            temperature
        )

        # Los 4 campos que debe devolver
        fields_to_extract = request_data.get("fields", [
            "procedimiento_trabajo",
            "proteccion_colectiva", 
            "factor_vla",
            "volatilidad"
        ])
        
        k = request_data.get("k", 4)  # Documentos por consulta
        requests_per_field = request_data.get("requests_per_field", 3)  # Requests por campo
        
        # Información del prompt maestra procesada
        prompt_info = {
            "template_length": len(master_prompt_template),
            "processed_length": len(master_prompt),
            "estimated_tokens": len(master_prompt.split()) * 1.3,
            "total_fields_to_extract": len(fields_to_extract),
            "placeholders_replaced": True,
            "chemical_analyzed": chemical_name,
            "temperature_provided": temperature
        }

        # Procesar cada campo
        results = {}
        
        for field in fields_to_extract:
            logger.info(f"Procesando campo: {field}")
            field_results = []
            
            # Hacer múltiples requests para el mismo campo
            for request_num in range(requests_per_field):
                
                # Crear prompt específico para este campo y request
                field_prompt = f"""
                PROMPT MAESTRA PROCESADA:
                {master_prompt}
                
                TAREA ESPECÍFICA:
                Analiza toda la información anterior y extrae específicamente el valor para: {field}
                
                REQUEST {request_num + 1}: Enfócate en identificar y extraer únicamente la información relacionada con {field}.
                Proporciona el valor, clasificación o dato específico para este campo.
                """
                
                # Hacer consulta RAG
                field_result = rag_faiss_model.answer_question(field_prompt, k=k)
                
                # Log del resultado RAG
                answer = field_result.get("answer", "")
                confidence = field_result.get("confidence", 0)
                sources_count = len(field_result.get("sources", []))
                
                logger.info(f"🤖 RAG RESULTADO campo {field} - request {request_num + 1}:")
                logger.info(f"   📝 RESPUESTA: {answer[:200]}..." if answer else "   📝 RESPUESTA: VACÍA")
                logger.info(f"   🎯 CONFIDENCE: {confidence}")
                logger.info(f"   📚 FUENTES: {sources_count}")
                
                # Almacenar resultado individual
                field_results.append({
                    "request_number": request_num + 1,
                    "answer": answer,
                    "sources": field_result.get("sources", []),
                    "confidence": confidence
                })
                
                logger.info(f"✅ Completado request {request_num + 1}/{requests_per_field} para campo: {field}")
            
            # Analizar resultados del campo
            answers = [r["answer"] for r in field_results]
            confidences = [r["confidence"] for r in field_results]
            all_sources = []
            for r in field_results:
                for source in r["sources"]:
                    if source not in all_sources:
                        all_sources.append(source)
            
            # Compilar resultados finales del campo
            results[field] = {
                "field_name": field,
                "total_requests": requests_per_field,
                "individual_results": field_results,
                "summary": {
                    "average_confidence": sum(confidences) / len(confidences) if confidences else 0,
                    "all_sources": all_sources,
                    "answer_consistency": len(set(ans[:100] for ans in answers)) <= 2,  # Tolerante
                    "most_detailed_answer": max(answers, key=len) if answers else "",
                    "shortest_answer": min(answers, key=len) if answers else "",
                    "answer_lengths": [len(ans) for ans in answers]
                }
            }

        return jsonify({
            "status": "success",
            "prompt_info": prompt_info,
            "fields_analyzed": fields_to_extract,
            "results": results,
            "processing_summary": {
                "total_fields": len(fields_to_extract),
                "requests_per_field": requests_per_field,
                "total_requests_made": len(fields_to_extract) * requests_per_field,
                "fields_with_consistent_answers": [
                    field for field, data in results.items() 
                    if data["summary"]["answer_consistency"]
                ],
                "average_confidence_overall": sum(
                    results[field]["summary"]["average_confidence"] 
                    for field in results
                ) / len(results) if results else 0
            }
        })

    except Exception as e:
        logger.error(f"Error en análisis de campos múltiples: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

def _process_master_prompt_with_chunks(template, chemical_name, temperature):
        """Procesar la prompt maestra reemplazando placeholders con chunks de FDS"""
        
        # PASO 1: Buscar chunks de FDS si se proporciona nombre químico
        fds_chunks = ""
        if chemical_name:
            # Buscar chunks específicos de FDS para este químico
            search_query = f"ficha datos seguridad {chemical_name} FDS propiedades físicas estado físico punto ebullición peligros frases H VLA"
            try:
                logger.info(f"🔍 BÚSQUEDA RAG PARA: {chemical_name}")
                logger.info(f"🔍 QUERY: {search_query}")
                
                docs = rag_faiss_model.search_documents(search_query, k=15)  # 10-15 chunks como especifica la prompt
                
                logger.info(f"🔍 DOCUMENTOS ENCONTRADOS: {len(docs) if docs else 0}")
                
                if docs:
                    logger.info(f"🔍 PRIMEROS 3 CHUNKS:")
                    for i, doc in enumerate(docs[:3]):
                        logger.info(f"   CHUNK {i+1}: {doc.page_content[:200]}...")
                    
                    fds_chunks = "\n\n".join([
                        f"CHUNK {i+1} - FDS {chemical_name.upper()}:\n{doc.page_content}" 
                        for i, doc in enumerate(docs[:15])
                    ])
                else:
                    logger.warning(f"❌ NO se encontraron chunks para {chemical_name}")
                    fds_chunks = f"[ADVERTENCIA: No se encontraron datos de FDS para {chemical_name} en la base de datos]"
                
                logger.info(f"📊 CHUNKS ENCONTRADOS: {len(docs)} para {chemical_name}")
                    
            except Exception as e:
                logger.error(f"❌ ERROR buscando FDS para {chemical_name}: {e}")
                fds_chunks = f"[ERROR: No se pudieron recuperar datos de FDS para {chemical_name}]"
        else:
            fds_chunks = "[ADVERTENCIA: No se proporcionó nombre de químico para buscar FDS]"
        
        # PASO 2: Reemplazar placeholders específicos en la prompt maestra
        processed_prompt = template.replace(
            "{aqui_insertas_los_10-15_chunks_de_la_FDS}", 
            fds_chunks
        )
        
        processed_prompt = processed_prompt.replace(
            "{aqui_insertas_la_temperatura_de_trabajo_o_No_proporcionada}",
            temperature
        )
        
        # Reemplazar otros placeholders posibles
        if "{chemical_name}" in processed_prompt:
            processed_prompt = processed_prompt.replace("{chemical_name}", chemical_name)
        
        logger.info(f"Prompt maestra procesada: {len(fds_chunks)} caracteres de FDS agregados, temperatura: {temperature}")
        
        return processed_prompt


# Manejador de errores para el Blueprint
@rag_faiss_bp.errorhandler(413)
def file_too_large(error):
    return (
        jsonify(
            {
                "status": "error",
                "message": f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024 * 1024)}MB",
            }
        ),
        413,
    )
