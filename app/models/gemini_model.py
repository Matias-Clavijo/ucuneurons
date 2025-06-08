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
        
        self.chat_sessions = {}  # Almacenar sesiones de chat
    
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
            
            self.chat_sessions[session_id] = {
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
        if session_id not in self.chat_sessions:
            return {
                "status": "error",
                "message": f"Sesión '{session_id}' no encontrada. Crear sesión primero.",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            chat = self.chat_sessions[session_id]["chat"]
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
        if session_id not in self.chat_sessions:
            yield f"Error: Sesión '{session_id}' no encontrada"
            return
        
        try:
            chat = self.chat_sessions[session_id]["chat"]
            response = chat.send_message_stream(message)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def get_chat_history(self, session_id: str) -> Dict[str, Any]:
        """Obtener historial de chat"""
        if session_id not in self.chat_sessions:
            return {
                "status": "error",
                "message": f"Sesión '{session_id}' no encontrada",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            chat = self.chat_sessions[session_id]["chat"]
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
        if session_id in self.chat_sessions:
            del self.chat_sessions[session_id]
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
        """Listar todas las sesiones de chat activas"""
        sessions_info = []
        for session_id, session_data in self.chat_sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "created_at": session_data["created_at"],
                "system_instruction": bool(session_data.get("system_instruction"))
            })
        
        return {
            "status": "success",
            "sessions": sessions_info,
            "total_sessions": len(sessions_info),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Obtener información del modelo actual"""
        return {
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_configured": bool(self.api_key),
            "client_active": bool(self.client),
            "active_sessions": len(self.chat_sessions)
        }

    # ======================
    # MÉTODOS DE RAG
    # ======================
    
    def query_with_context(self, query: str, context: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Realizar consulta con contexto específico (RAG)"""
        if not self.client:
            return {
                "status": "error",
                "message": "Gemini API no está configurada. Verifica GEMINI_API_KEY en .env",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            prompt = self._build_prompt(query, context)
            
            config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                temperature=temperature
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            return {
                "status": "success",
                "response": response.text,
                "query": query,
                "context_length": len(context),
                "temperature": temperature,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Fallback response en caso de error
            fallback = self._fallback_response(query)
            return {
                "status": "error",
                "message": str(e),
                "fallback_response": fallback,
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def query_without_context(self, query: str, temperature: float = 0.7) -> Dict[str, Any]:
        """Realizar consulta sin contexto específico"""
        if not self.client:
            return {
                "status": "error",
                "message": "Gemini API no está configurada. Verifica GEMINI_API_KEY en .env",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            config = types.GenerateContentConfig(
                max_output_tokens=self.max_tokens,
                temperature=temperature
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=query,
                config=config
            )
            
            return {
                "status": "success",
                "response": response.text,
                "query": query,
                "temperature": temperature,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    def chat_with_context(self, session_id: str, message: str, context: str, temperature: float = 0.1) -> Dict[str, Any]:
        """Chat con contexto específico (RAG conversacional)"""
        if session_id not in self.chat_sessions:
            # Crear sesión si no existe
            system_instruction = f"""Eres un asistente especializado. 
            Utiliza el siguiente contexto para responder consultas de forma precisa y útil:
            
            CONTEXTO:
            {context}
            
            Responde basándote en este contexto siempre que sea relevante."""
            
            create_result = self.create_chat_session(session_id, system_instruction)
            if create_result["status"] == "error":
                return create_result
        
        try:
            chat = self.chat_sessions[session_id]["chat"]
            response = chat.send_message(message)
            
            return {
                "status": "success",
                "response": response.text,
                "user_message": message,
                "session_id": session_id,
                "context_length": len(context),
                "temperature": temperature,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            fallback = self._fallback_response(message)
            return {
                "status": "error",
                "message": str(e),
                "fallback_response": fallback,
                "user_message": message,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def summarize_document(self, content: str, max_length: int = 500) -> Dict[str, Any]:
        """Resumir documento o contenido largo"""
        if not self.client:
            return {
                "status": "error",
                "message": "Gemini API no está configurada. Verifica GEMINI_API_KEY en .env",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            prompt = f"""Resume el siguiente contenido en máximo {max_length} palabras.
            Incluye los puntos más importantes y mantén la información clave:
            
            CONTENIDO:
            {content}
            
            RESUMEN:"""
            
            config = types.GenerateContentConfig(
                max_output_tokens=min(self.max_tokens, max_length * 2),
                temperature=0.1
            )
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            return {
                "status": "success",
                "summary": response.text,
                "original_length": len(content),
                "summary_length": len(response.text),
                "max_length": max_length,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "content_length": len(content),
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Construir prompt con contexto para RAG"""
        return f"""Eres un asistente especializado que responde preguntas basándose en el contexto proporcionado.

CONTEXTO:
{context}

PREGUNTA: {query}

INSTRUCCIONES:
- Responde únicamente basándote en la información del contexto
- Si la información no está en el contexto, indica que no tienes suficiente información
- Sé preciso y conciso en tu respuesta
- Cita información específica del contexto cuando sea relevante

RESPUESTA:"""
    
    def _fallback_response(self, query: str) -> str:
        """Generar respuesta de fallback cuando hay errores"""
        return f"""Lo siento, no pude procesar tu consulta '{query}' en este momento debido a un error técnico. 
        Por favor, intenta reformular tu pregunta o contacta al administrador del sistema."""
    
    def is_available(self) -> bool:
        """Verificar si el servicio está disponible"""
        return bool(self.client and self.api_key)

# Instancia global del modelo Gemini
gemini_model = GeminiModel()
