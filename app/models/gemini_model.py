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