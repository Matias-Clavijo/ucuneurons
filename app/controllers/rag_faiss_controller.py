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
