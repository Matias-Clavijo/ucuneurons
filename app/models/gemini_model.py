from typing import List, Dict, Any, Optional, Iterator
import io
import base64
from datetime import datetime
from PIL import Image
from google import genai
from google.genai import types
from app.config.config import Config

class GeminiModel:
    """Modelo para manejar las interacciones con Gemini AI"""
    
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        self.model_name = Config.GEMINI_MODEL
        self.max_tokens = Config.GEMINI_MAX_TOKENS
        self.temperature = Config.GEMINI_TEMPERATURE
        
        if not self.api_key:
            print("⚠️  ADVERTENCIA: GEMINI_API_KEY no está configurada.")
            print("   Configura la variable en tu archivo .env:")
            print("   GEMINI_API_KEY=tu_api_key_aqui")
            self.client = None
        else:
            self.client = genai.Client(api_key=self.api_key)
        
        self._chat_sessions = {}  # Almacenar sesiones de chat
    
    def generate_text(self, prompt: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """Generar texto usando Gemini"""
        if not self.client:
            return {
                "status": "error",
                "message": "Gemini API no está configurada. Verifica GEMINI_API_KEY en .env",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if system_instruction:
                config.system_instruction = system_instruction
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
                config=config
            )
            
            return {
                "status": "success",
                "text": response.text,
                "prompt": prompt,
                "system_instruction": system_instruction,
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name,
                "config": {
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_text_stream(self, prompt: str, system_instruction: Optional[str] = None) -> Iterator[str]:
        """Generar texto con streaming"""
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if system_instruction:
                config.system_instruction = system_instruction
            
            response = self.client.models.generate_content_stream(
                model=self.model_name,
                contents=[prompt],
                config=config
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def create_chat_session(self, session_id: str, system_instruction: Optional[str] = None) -> Dict[str, Any]:
        """Crear una nueva sesión de chat"""
        if not self.client:
            return {
                "status": "error",
                "message": "Gemini API no está configurada. Verifica GEMINI_API_KEY en .env",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if system_instruction:
                config.system_instruction = system_instruction
            
            chat = self.client.chats.create(
                model=self.model_name,
                config=config
            )
            
            self._chat_sessions[session_id] = {
                "chat": chat,
                "created_at": datetime.now().isoformat(),
                "system_instruction": system_instruction
            }
            
            return {
                "status": "success",
                "session_id": session_id,
                "message": "Sesión de chat creada exitosamente",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def send_chat_message(self, session_id: str, message: str) -> Dict[str, Any]:
        """Enviar mensaje en una sesión de chat"""
        if session_id not in self._chat_sessions:
            return {
                "status": "error",
                "message": f"Sesión '{session_id}' no encontrada. Crear sesión primero.",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            chat = self._chat_sessions[session_id]["chat"]
            response = chat.send_message(message)
            
            return {
                "status": "success",
                "response": response.text,
                "user_message": message,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "user_message": message,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def send_chat_message_stream(self, session_id: str, message: str) -> Iterator[str]:
        """Enviar mensaje con streaming en chat"""
        if session_id not in self._chat_sessions:
            yield f"Error: Sesión '{session_id}' no encontrada"
            return
        
        try:
            chat = self._chat_sessions[session_id]["chat"]
            response = chat.send_message_stream(message)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Obtener historial de chat"""
        if session_id not in self._chat_sessions:
            return {
                "status": "error",
                "message": f"Sesión '{session_id}' no encontrada",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            chat = self._chat_sessions[session_id]["chat"]
            history = []
            
            for message in chat.get_history():
                history.append({
                    "role": message.role,
                    "content": message.parts[0].text if message.parts else "",
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                "status": "success",
                "session_id": session_id,
                "history": history,
                "total_messages": len(history),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def analyze_image(self, image_data: bytes, prompt: str = "Describe esta imagen") -> Dict[str, Any]:
        """Analizar imagen usando Gemini Vision"""
        try:
            # Convertir bytes a imagen PIL
            image = Image.open(io.BytesIO(image_data))
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[image, prompt]
            )
            
            return {
                "status": "success",
                "analysis": response.text,
                "prompt": prompt,
                "timestamp": datetime.now().isoformat(),
                "model": self.model_name
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "prompt": prompt,
                "timestamp": datetime.now().isoformat()
            }
    
    def delete_chat_session(self, session_id: str) -> Dict[str, Any]:
        """Eliminar sesión de chat"""
        if session_id in self._chat_sessions:
            del self._chat_sessions[session_id]
            return {
                "status": "success",
                "message": f"Sesión '{session_id}' eliminada",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": f"Sesión '{session_id}' no encontrada",
                "timestamp": datetime.now().isoformat()
            }
    
    def list_chat_sessions(self) -> Dict[str, Any]:
        """Listar todas las sesiones de chat"""
        sessions = []
        for session_id, session_data in self._chat_sessions.items():
            sessions.append({
                "session_id": session_id,
                "created_at": session_data["created_at"],
                "system_instruction": session_data.get("system_instruction", "None")
            })
        
        return {
            "status": "success",
            "sessions": sessions,
            "total_sessions": len(sessions),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo"""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_configured": bool(self.api_key),
            "active_sessions": len(self._chat_sessions),
            "timestamp": datetime.now().isoformat()
        }

# Instancia global del modelo Gemini
gemini_model = GeminiModel() 
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
