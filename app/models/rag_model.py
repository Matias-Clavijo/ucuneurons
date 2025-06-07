import os
import hashlib
import tempfile
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
import logging

# RAG and Vector Database
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Document Processing
import PyPDF2
import pdfplumber
from docx import Document as DocxDocument

# Image Processing
from PIL import Image
import pytesseract
import cv2
import numpy as np

# Utilities
import magic
import tiktoken


logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Procesador de documentos para extraer texto de diferentes formatos"""

    def __init__(self):
        self.supported_formats = {
            "pdf": self._process_pdf,
            "docx": self._process_docx,
            "txt": self._process_txt,
            "image": self._process_image,
        }

    def process_file(
        self, file_path: str, file_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Procesar un archivo y extraer su contenido"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

            # Detectar tipo de archivo si no se proporciona
            if not file_type:
                file_type = self._detect_file_type(file_path)

            # Procesar según el tipo de archivo
            if file_type in self.supported_formats:
                content = self.supported_formats[file_type](file_path)

                return {
                    "content": content,
                    "file_path": file_path,
                    "file_type": file_type,
                    "processed_at": datetime.now().isoformat(),
                    "content_length": len(content),
                    "word_count": len(content.split()) if content else 0,
                }
            else:
                raise ValueError(f"Tipo de archivo no soportado: {file_type}")

        except Exception as e:
            logger.error(f"Error procesando archivo {file_path}: {str(e)}")
            raise

    def _detect_file_type(self, file_path: str) -> str:
        """Detectar el tipo de archivo"""
        try:
            mime = magic.from_file(file_path, mime=True)

            if mime == "application/pdf":
                return "pdf"
            elif (
                mime
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return "docx"
            elif mime.startswith("text/"):
                return "txt"
            elif mime.startswith("image/"):
                return "image"
            else:
                # Fallback basado en extensión
                ext = os.path.splitext(file_path)[1].lower()
                if ext == ".pdf":
                    return "pdf"
                elif ext == ".docx":
                    return "docx"
                elif ext in [".txt", ".md"]:
                    return "txt"
                elif ext in [".jpg", ".jpeg", ".png", ".bmp", ".tiff"]:
                    return "image"
                else:
                    raise ValueError(f"Tipo de archivo no reconocido: {ext}")

        except Exception as e:
            logger.warning(f"Error detectando tipo de archivo: {str(e)}")
            # Intentar por extensión como último recurso
            ext = os.path.splitext(file_path)[1].lower()
            type_map = {
                ".pdf": "pdf",
                ".docx": "docx",
                ".txt": "txt",
                ".md": "txt",
                ".jpg": "image",
                ".jpeg": "image",
                ".png": "image",
            }
            return type_map.get(ext, "unknown")

    def _process_pdf(self, file_path: str) -> str:
        """Extraer texto de archivos PDF"""
        text_content = []

        try:
            # Intentar con pdfplumber primero (mejor para tablas y layouts complejos)
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
        except Exception as e:
            logger.warning(f"Error con pdfplumber: {str(e)}, intentando con PyPDF2...")

            # Fallback a PyPDF2
            try:
                with open(file_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text_content.append(page.extract_text())
            except Exception as e2:
                logger.error(f"Error también con PyPDF2: {str(e2)}")
                raise

        return "\n".join(text_content)

    def _process_docx(self, file_path: str) -> str:
        """Extraer texto de archivos DOCX"""
        doc = DocxDocument(file_path)
        paragraphs = [paragraph.text for paragraph in doc.paragraphs]
        return "\n".join(paragraphs)

    def _process_txt(self, file_path: str) -> str:
        """Leer archivos de texto plano"""
        encodings = ["utf-8", "latin-1", "cp1252"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as file:
                    return file.read()
            except UnicodeDecodeError:
                continue

        raise ValueError(f"No se pudo decodificar el archivo de texto: {file_path}")

    def _process_image(self, file_path: str) -> str:
        """Extraer texto de imágenes usando OCR"""
        try:
            # Cargar imagen
            image = cv2.imread(file_path)
            if image is None:
                # Intentar con PIL
                pil_image = Image.open(file_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

            # Preprocesamiento de imagen para mejorar OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Aplicar filtros para mejorar la calidad
            denoised = cv2.fastNlMeansDenoising(gray)

            # Binarización adaptativa
            binary = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Extraer texto usando Tesseract
            custom_config = r"--oem 3 --psm 6"
            text = pytesseract.image_to_string(
                binary, config=custom_config, lang="spa+eng"
            )

            return text.strip()

        except Exception as e:
            logger.error(f"Error en OCR de imagen {file_path}: {str(e)}")
            raise


class RAGModel:
    """Modelo principal para Retrieval-Augmented Generation usando ChromaDB"""

    def __init__(
        self,
        collection_name: str = "documents",
        chroma_host: str = "localhost",
        chroma_port: int = 8000,
        use_http: bool = True,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):

        self.collection_name = collection_name
        self.chroma_host = chroma_host
        self.chroma_port = chroma_port
        self.use_http = use_http
        self.embedding_model_name = embedding_model

        # Inicializar ChromaDB client
        self.client = None
        if use_http:
            try:
                # Conectar al servicio ChromaDB via HTTP
                self.client = chromadb.HttpClient(
                    host=chroma_host,
                    port=chroma_port,
                    settings=Settings(anonymized_telemetry=False),
                )
                logger.info(
                    f"Conectando a ChromaDB en http://{chroma_host}:{chroma_port}"
                )

                # Probar la conexión
                self.client.heartbeat()
                logger.info("Conexión a ChromaDB HTTP exitosa")

            except Exception as e:
                logger.warning(f"No se pudo conectar a ChromaDB HTTP: {str(e)}")
                logger.info("Usando ChromaDB local como fallback")
                use_http = False

        if not use_http or self.client is None:
            # Usar cliente persistente local (fallback)
            persist_directory = "./chroma_db"
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(
                path=persist_directory, settings=Settings(anonymized_telemetry=False)
            )
            logger.info(f"Usando ChromaDB local en {persist_directory}")

        # Obtener o crear colección
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Colección '{collection_name}' cargada")
        except Exception as e:
            # La colección no existe, crearla
            try:
                self.collection = self.client.create_collection(name=collection_name)
                logger.info(f"Colección '{collection_name}' creada")
            except Exception as create_error:
                logger.error(f"Error creando colección: {create_error}")
                raise

        # Inicializar modelo de embeddings
        self.embedding_model = SentenceTransformer(embedding_model)

        # Inicializar procesador de documentos
        self.doc_processor = DocumentProcessor()

        # Tokenizer para contar tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def ingest_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Dict[str, Any]:
        """Ingestar un documento en la base de datos vectorial"""
        try:
            # Procesar el documento
            doc_data = self.doc_processor.process_file(file_path)
            content = doc_data["content"]

            if not content.strip():
                raise ValueError("El documento no contiene texto extraíble")

            # Crear chunks del contenido
            chunks = self._create_chunks(content, chunk_size, chunk_overlap)

            # Generar ID único para el documento
            doc_id = self._generate_document_id(file_path, content)

            # Preparar metadatos
            doc_metadata = {
                "document_id": doc_id,
                "file_path": file_path,
                "file_type": doc_data["file_type"],
                "processed_at": doc_data["processed_at"],
                "total_chunks": len(chunks),
                "content_length": doc_data["content_length"],
                "word_count": doc_data["word_count"],
            }

            if metadata:
                doc_metadata.update(metadata)

            # Preparar datos para ChromaDB
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []

            for i, chunk in enumerate(chunks):
                chunk_id = f"{doc_id}_chunk_{i}"
                chunk_metadata = doc_metadata.copy()
                chunk_metadata.update(
                    {
                        "chunk_index": i,
                        "chunk_id": chunk_id,
                        "chunk_text_length": len(chunk),
                        "chunk_token_count": len(self.tokenizer.encode(chunk)),
                    }
                )

                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                chunk_metadatas.append(chunk_metadata)

            # Insertar en ChromaDB
            self.collection.add(
                documents=chunk_texts, metadatas=chunk_metadatas, ids=chunk_ids
            )

            result = {
                "status": "success",
                "document_id": doc_id,
                "file_path": file_path,
                "file_type": doc_data["file_type"],
                "chunks_created": len(chunks),
                "total_tokens": sum(
                    len(self.tokenizer.encode(chunk)) for chunk in chunks
                ),
                "processed_at": datetime.now().isoformat(),
            }

            logger.info(f"Documento ingestado exitosamente: {doc_id}")
            return result

        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {str(e)}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Buscar documentos similares a la consulta"""
        try:
            # Preparar filtros
            where_clause = filter_metadata if filter_metadata else None

            # Realizar búsqueda
            results = self.collection.query(
                query_texts=[query], n_results=n_results, where=where_clause
            )

            # Formatear resultados
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    result_item = {
                        "content": doc,
                        "metadata": (
                            results["metadatas"][0][i] if results["metadatas"] else {}
                        ),
                        "distance": (
                            results["distances"][0][i] if results["distances"] else 0.0
                        ),
                        "id": results["ids"][0][i] if results["ids"] else None,
                    }
                    formatted_results.append(result_item)

            return {
                "status": "success",
                "query": query,
                "results": formatted_results,
                "total_results": len(formatted_results),
                "searched_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error en búsqueda: {str(e)}")
            raise

    def get_context_for_query(
        self, query: str, max_tokens: int = 4000, n_results: int = 10
    ) -> str:
        """Obtener contexto relevante para una consulta (para usar con Gemini)"""
        try:
            search_results = self.search(query, n_results=n_results)

            context_parts = []
            current_tokens = 0

            for result in search_results["results"]:
                content = result["content"]
                tokens = len(self.tokenizer.encode(content))

                if current_tokens + tokens <= max_tokens:
                    context_parts.append(content)
                    current_tokens += tokens
                else:
                    # Si no cabe completo, intentar agregar una parte
                    remaining_tokens = max_tokens - current_tokens
                    if remaining_tokens > 100:  # Solo si quedan suficientes tokens
                        truncated_content = self._truncate_to_tokens(
                            content, remaining_tokens
                        )
                        context_parts.append(truncated_content)
                    break

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error obteniendo contexto: {str(e)}")
            return ""

    def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Eliminar un documento de la base de datos"""
        try:
            # Buscar todos los chunks del documento
            results = self.collection.query(
                query_texts=[""],  # Query vacío
                n_results=1000,  # Número alto para obtener todos los chunks
                where={"document_id": document_id},
            )

            if not results["ids"] or not results["ids"][0]:
                return {
                    "status": "error",
                    "message": f"Documento {document_id} no encontrado",
                }

            # Eliminar todos los chunks
            chunk_ids = results["ids"][0]
            self.collection.delete(ids=chunk_ids)

            return {
                "status": "success",
                "document_id": document_id,
                "chunks_deleted": len(chunk_ids),
                "deleted_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error eliminando documento {document_id}: {str(e)}")
            raise

    def list_documents(self) -> Dict[str, Any]:
        """Listar todos los documentos en la base de datos"""
        try:
            # Obtener todos los metadatos únicos por document_id
            all_results = self.collection.get()

            documents = {}
            for metadata in all_results["metadatas"]:
                doc_id = metadata.get("document_id")
                if doc_id and doc_id not in documents:
                    documents[doc_id] = {
                        "document_id": doc_id,
                        "file_path": metadata.get("file_path"),
                        "file_type": metadata.get("file_type"),
                        "processed_at": metadata.get("processed_at"),
                        "total_chunks": metadata.get("total_chunks", 0),
                        "content_length": metadata.get("content_length", 0),
                        "word_count": metadata.get("word_count", 0),
                    }

            return {
                "status": "success",
                "documents": list(documents.values()),
                "total_documents": len(documents),
                "retrieved_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error listando documentos: {str(e)}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la colección"""
        try:
            count = self.collection.count()

            return {
                "collection_name": self.collection_name,
                "total_chunks": count,
                "embedding_model": self.embedding_model_name,
                "chroma_host": self.chroma_host,
                "chroma_port": self.chroma_port,
                "use_http": self.use_http,
                "connection_type": "HTTP" if self.use_http else "Local",
            }

        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            raise

    def _create_chunks(
        self, text: str, chunk_size: int, chunk_overlap: int
    ) -> List[str]:
        """Dividir texto en chunks con overlap"""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size

            # Si no es el último chunk, buscar un punto de corte natural
            if end < text_length:
                # Buscar el último espacio dentro del rango permitido
                last_space = text.rfind(" ", start, end)
                if last_space > start:
                    end = last_space

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Calcular el próximo inicio con overlap
            start = end - chunk_overlap
            if start <= 0:
                start = end

        return chunks

    def _generate_document_id(self, file_path: str, content: str) -> str:
        """Generar un ID único para el documento"""
        # Usar hash del contenido + filename para generar ID único
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        return f"{filename}_{timestamp}_{content_hash}"

    def _truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncar texto para que no exceda el número máximo de tokens"""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text

        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens)


# Inicializar modelo RAG con configuración desde variables de entorno
def _create_rag_model():
    """Factory function para crear la instancia del modelo RAG"""
    from app.config.config import Config

    return RAGModel(
        collection_name=Config.RAG_COLLECTION_NAME,
        chroma_host=Config.CHROMA_HOST,
        chroma_port=Config.CHROMA_PORT,
        use_http=Config.CHROMA_USE_HTTP,
        embedding_model=Config.RAG_EMBEDDING_MODEL,
    )


# Instancia global del modelo RAG
rag_model = _create_rag_model()
