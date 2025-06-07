import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    import google.generativeai as genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Generative AI SDK no está instalado")

from .rag_model import rag_model


logger = logging.getLogger(__name__)


class GeminiModel:
    """Modelo para integrar con Gemini utilizando contexto de RAG"""

    def __init__(self, model_name: Optional[str] = None):
        # Si no se especifica modelo, usar el de configuración o el por defecto
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.model = None
        self.rag_model = rag_model

        # Configurar Gemini si está disponible
        if GEMINI_AVAILABLE:
            self._initialize_gemini()
        else:
            logger.warning(
                "Gemini SDK no disponible. Las funciones de IA estarán limitadas."
            )

    def _initialize_gemini(self):
        """Inicializar la conexión con Gemini"""
        try:
            # Obtener API key desde variable de entorno
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error(
                    "GEMINI_API_KEY no está configurada en las variables de entorno"
                )
                return

            # Configurar la API
            genai.configure(api_key=api_key)

            # Inicializar el modelo
            self.model = genai.GenerativeModel(self.model_name)

            logger.info(f"Gemini {self.model_name} inicializado exitosamente")

        except Exception as e:
            logger.error(f"Error inicializando Gemini: {str(e)}")
            self.model = None

    def query_with_context(
        self,
        query: str,
        max_context_tokens: int = 4000,
        search_results: int = 10,
        system_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Realizar consulta a Gemini con contexto de RAG"""
        try:
            if not self.model:
                return self._fallback_response(query)

            # Obtener contexto relevante del RAG
            context = self.rag_model.get_context_for_query(
                query=query, max_tokens=max_context_tokens, n_results=search_results
            )

            # Construir el prompt completo
            full_prompt = self._build_prompt(query, context, system_prompt)

            # Realizar la consulta a Gemini
            response = self.model.generate_content(full_prompt)

            # Obtener metadatos de la búsqueda RAG
            search_metadata = self.rag_model.search(query, n_results=search_results)

            return {
                "status": "success",
                "query": query,
                "response": response.text,
                "context_used": bool(context),
                "context_length": len(context) if context else 0,
                "sources": [
                    {
                        "id": result["id"],
                        "file_path": result["metadata"].get("file_path"),
                        "file_type": result["metadata"].get("file_type"),
                        "distance": result["distance"],
                    }
                    for result in search_metadata["results"]
                ],
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
            }

        except Exception as e:
            logger.error(f"Error en consulta con contexto: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "fallback_response": self._fallback_response(query),
            }

    def query_without_context(
        self, query: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Realizar consulta directa a Gemini sin contexto de RAG"""
        try:
            if not self.model:
                return self._fallback_response(query)

            # Construir prompt sin contexto
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUsuario: {query}"
            else:
                full_prompt = query

            # Realizar la consulta a Gemini
            response = self.model.generate_content(full_prompt)

            return {
                "status": "success",
                "query": query,
                "response": response.text,
                "context_used": False,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
            }

        except Exception as e:
            logger.error(f"Error en consulta sin contexto: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "fallback_response": self._fallback_response(query),
            }

    def chat_with_context(
        self, messages: List[Dict[str, str]], max_context_tokens: int = 3000
    ) -> Dict[str, Any]:
        """Mantener una conversación con contexto de RAG basado en el último mensaje"""
        try:
            if not self.model:
                return self._fallback_response("Chat no disponible")

            if not messages:
                return {"status": "error", "message": "No hay mensajes"}

            # Obtener el último mensaje del usuario
            last_message = messages[-1]["content"]

            # Obtener contexto para el último mensaje
            context = self.rag_model.get_context_for_query(
                query=last_message, max_tokens=max_context_tokens, n_results=8
            )

            # Construir historial de conversación
            conversation_history = "\n".join(
                [f"{msg['role']}: {msg['content']}" for msg in messages[:-1]]
            )

            # Construir prompt completo con historial y contexto
            prompt_parts = []

            if context:
                prompt_parts.append(
                    f"Contexto relevante de los documentos:\n{context}\n"
                )

            if conversation_history:
                prompt_parts.append(
                    f"Historial de conversación:\n{conversation_history}\n"
                )

            prompt_parts.append(f"Usuario: {last_message}")

            full_prompt = "\n".join(prompt_parts)

            # Generar respuesta
            response = self.model.generate_content(full_prompt)

            return {
                "status": "success",
                "response": response.text,
                "context_used": bool(context),
                "context_length": len(context) if context else 0,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
            }

        except Exception as e:
            logger.error(f"Error en chat con contexto: {str(e)}")
            return {"status": "error", "message": str(e)}

    def summarize_document(self, document_id: str) -> Dict[str, Any]:
        """Generar un resumen de un documento específico"""
        try:
            if not self.model:
                return self._fallback_response("Resumen no disponible")

            # Obtener contenido del documento
            document_content = self.rag_model.get_document_content(document_id)

            if not document_content:
                return {"status": "error", "message": "Documento no encontrado"}

            # Prompt para resumir
            prompt = f"""
Por favor, genera un resumen conciso y comprensivo del siguiente documento:

--- DOCUMENTO ---
{document_content}
--- FIN DOCUMENTO ---

El resumen debe:
- Capturar los puntos principales y conceptos clave
- Ser claro y bien estructurado
- Mantener un tono profesional
- Tener aproximadamente 200-300 palabras
"""

            # Generar resumen
            response = self.model.generate_content(prompt)

            return {
                "status": "success",
                "document_id": document_id,
                "summary": response.text,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
            }

        except Exception as e:
            logger.error(f"Error generando resumen: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _build_prompt(
        self, query: str, context: str, system_prompt: Optional[str] = None
    ) -> str:
        """Construir el prompt completo para Gemini"""
        prompt_parts = []

        # Sistema prompt por defecto si no se proporciona uno
        if not system_prompt:
            system_prompt = """Eres un asistente inteligente que ayuda a responder preguntas basándose en documentos proporcionados como contexto.

Instrucciones:
1. Utiliza principalmente la información del contexto proporcionado para responder
2. Si la información no está en el contexto, indícalo claramente
3. Proporciona respuestas claras, precisas y bien estructuradas
4. Cita las fuentes cuando sea relevante
5. Si la pregunta no puede ser respondida con el contexto, ofrece una respuesta general útil"""

        prompt_parts.append(system_prompt)

        if context:
            prompt_parts.append(f"\nContexto de los documentos:\n{context}")

        prompt_parts.append(f"\nPregunta del usuario: {query}")
        prompt_parts.append("\nRespuesta:")

        return "\n".join(prompt_parts)

    def _fallback_response(self, query: str) -> Dict[str, Any]:
        """Respuesta de respaldo cuando Gemini no está disponible"""
        return {
            "status": "success",
            "query": query,
            "response": "Lo siento, el servicio de IA no está disponible en este momento. Por favor, verifica la configuración de la API de Gemini.",
            "context_used": False,
            "fallback": True,
            "generated_at": datetime.now().isoformat(),
            "model_used": "fallback",
        }

    def is_available(self) -> bool:
        """Verificar si Gemini está disponible y configurado"""
        return GEMINI_AVAILABLE and self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información sobre el modelo"""
        return {
            "model_name": self.model_name,
            "available": self.is_available(),
            "gemini_sdk_installed": GEMINI_AVAILABLE,
            "api_key_configured": bool(os.getenv("GEMINI_API_KEY")),
        }


# Instancia global del modelo Gemini
gemini_model = GeminiModel()
