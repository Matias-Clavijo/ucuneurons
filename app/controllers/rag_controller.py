import os
import tempfile
import logging
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from app.models.rag_model import rag_model
from app.models.gemini_model import gemini_model


logger = logging.getLogger(__name__)

# Crear Blueprint para RAG endpoints
rag_bp = Blueprint("rag", __name__)

# Configuración de archivos permitidos
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md", "jpg", "jpeg", "png", "bmp", "tiff"}

MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB


def allowed_file(filename):
    """Verificar si el archivo tiene una extensión permitida"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_file_size(file):
    """Validar el tamaño del archivo"""
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    return file_size <= MAX_FILE_SIZE


@rag_bp.route("/")
def rag_home():
    """Información de los endpoints RAG disponibles"""
    return jsonify(
        {
            "message": "Endpoints RAG disponibles",
            "version": "1.0.0",
            "endpoints": [
                "POST /api/rag/ingest - Ingestar documento",
                "GET  /api/rag/documents - Listar documentos",
                "DELETE /api/rag/documents/<document_id> - Eliminar documento",
                "POST /api/rag/search - Buscar en documentos",
                "POST /api/rag/query - Consulta con contexto RAG",
                "POST /api/rag/chat - Chat con contexto RAG",
                "POST /api/rag/summarize/<document_id> - Resumir documento",
                "GET  /api/rag/stats - Estadísticas de la colección",
                "GET  /api/rag/health - Estado del sistema RAG",
            ],
            "supported_formats": list(ALLOWED_EXTENSIONS),
            "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
        }
    )


@rag_bp.route("/ingest", methods=["POST"])
def ingest_document():
    """Ingestar un documento en la base de datos RAG"""
    try:
        # Verificar si se envió un archivo
        if "file" not in request.files:
            return (
                jsonify(
                    {"status": "error", "message": "No se proporcionó ningún archivo"}
                ),
                400,
            )

        file = request.files["file"]

        # Verificar si se seleccionó un archivo
        if file.filename == "":
            return (
                jsonify(
                    {"status": "error", "message": "No se seleccionó ningún archivo"}
                ),
                400,
            )

        # Verificar extensión del archivo
        if not allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Tipo de archivo no permitido. Formatos soportados: {', '.join(ALLOWED_EXTENSIONS)}",
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
                        "message": f"El archivo excede el tamaño máximo de {MAX_FILE_SIZE // (1024 * 1024)}MB",
                    }
                ),
                400,
            )

        # Obtener parámetros opcionales
        chunk_size = request.form.get("chunk_size", 1000, type=int)
        chunk_overlap = request.form.get("chunk_overlap", 200, type=int)

        # Metadatos adicionales
        metadata = {}
        if request.form.get("title"):
            metadata["title"] = request.form.get("title")
        if request.form.get("author"):
            metadata["author"] = request.form.get("author")
        if request.form.get("category"):
            metadata["category"] = request.form.get("category")
        if request.form.get("tags"):
            metadata["tags"] = request.form.get("tags").split(",")

        # Guardar archivo temporalmente
        filename = secure_filename(file.filename)
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, filename)

        try:
            file.save(temp_path)

            # Ingestar el documento
            result = rag_model.ingest_document(
                file_path=temp_path,
                metadata=metadata,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

            return jsonify(result)

        finally:
            # Limpiar archivo temporal
            try:
                os.remove(temp_path)
                os.rmdir(temp_dir)
            except OSError:
                pass

    except Exception as e:
        logger.error(f"Error en ingestión de documento: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/documents", methods=["GET"])
def list_documents():
    """Listar todos los documentos en la base de datos"""
    try:
        result = rag_model.list_documents()
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error listando documentos: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/documents/<document_id>", methods=["DELETE"])
def delete_document(document_id):
    """Eliminar un documento de la base de datos"""
    try:
        result = rag_model.delete_document(document_id)

        if result["status"] == "error":
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error eliminando documento: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/search", methods=["POST"])
def search_documents():
    """Buscar documentos similares a una consulta"""
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

        n_results = request_data.get("n_results", 5)
        filter_metadata = request_data.get("filter", None)

        result = rag_model.search(
            query=query, n_results=n_results, filter_metadata=filter_metadata
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/query", methods=["POST"])
def query_with_context():
    """Realizar consulta a Gemini con contexto de RAG"""
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

        max_context_tokens = request_data.get("max_context_tokens", 4000)
        search_results = request_data.get("search_results", 10)
        system_prompt = request_data.get("system_prompt", None)

        result = gemini_model.query_with_context(
            query=query,
            max_context_tokens=max_context_tokens,
            search_results=search_results,
            system_prompt=system_prompt,
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error en consulta con contexto: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/query-direct", methods=["POST"])
def query_without_context():
    """Realizar consulta directa a Gemini sin contexto de RAG"""
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

        system_prompt = request_data.get("system_prompt", None)

        result = gemini_model.query_without_context(
            query=query, system_prompt=system_prompt
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error en consulta directa: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/chat", methods=["POST"])
def chat_with_context():
    """Mantener una conversación con contexto de RAG"""
    try:
        request_data = request.get_json()
        if not request_data:
            return (
                jsonify({"status": "error", "message": "No se proporcionaron datos"}),
                400,
            )

        messages = request_data.get("messages", [])
        if not messages:
            return (
                jsonify(
                    {"status": "error", "message": "No se proporcionaron mensajes"}
                ),
                400,
            )

        max_context_tokens = request_data.get("max_context_tokens", 3000)

        result = gemini_model.chat_with_context(
            messages=messages, max_context_tokens=max_context_tokens
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error en chat: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/summarize/<document_id>", methods=["POST"])
def summarize_document(document_id):
    """Generar un resumen de un documento específico"""
    try:
        result = gemini_model.summarize_document(document_id)

        if result["status"] == "error" and "no encontrado" in result.get("message", ""):
            return jsonify(result), 404

        return jsonify(result)

    except Exception as e:
        logger.error(f"Error generando resumen: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/stats", methods=["GET"])
def get_collection_stats():
    """Obtener estadísticas de la colección RAG"""
    try:
        rag_stats = rag_model.get_collection_stats()
        gemini_info = gemini_model.get_model_info()

        return jsonify(
            {
                "status": "success",
                "rag": rag_stats,
                "gemini": gemini_info,
                "retrieved_at": rag_stats.get("retrieved_at"),
            }
        )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rag_bp.route("/health", methods=["GET"])
def health_check():
    """Verificar el estado del sistema RAG"""
    try:
        # Verificar RAG
        rag_healthy = True
        rag_error = None
        try:
            rag_model.get_collection_stats()
        except Exception as e:
            rag_healthy = False
            rag_error = str(e)

        # Verificar Gemini
        gemini_info = gemini_model.get_model_info()

        health_status = {
            "status": (
                "healthy" if rag_healthy and gemini_info["available"] else "degraded"
            ),
            "rag": {"healthy": rag_healthy, "error": rag_error},
            "gemini": gemini_info,
            "supported_formats": list(ALLOWED_EXTENSIONS),
            "max_file_size_mb": MAX_FILE_SIZE // (1024 * 1024),
            "checked_at": rag_model.get_collection_stats().get("retrieved_at"),
        }

        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code

    except Exception as e:
        logger.error(f"Error en health check: {str(e)}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


# Manejador de errores para el Blueprint
@rag_bp.errorhandler(413)
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


@rag_bp.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Endpoint RAG no encontrado"}), 404


@rag_bp.errorhandler(405)
def method_not_allowed(error):
    return (
        jsonify(
            {"status": "error", "message": "Método no permitido para este endpoint RAG"}
        ),
        405,
    )
