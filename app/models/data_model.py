from typing import List, Dict, Any
import json
from datetime import datetime

class DataModel:
    """Modelo para manejar los datos de la aplicación"""
    
    def __init__(self):
        self._data_store = {
            "messages": [],
            "counter": 0,
            "history": []
        }
    
    def get_all_data(self) -> Dict[str, Any]:
        """Obtener todos los datos"""
        return self._data_store.copy()
    
    def get_messages(self) -> List[str]:
        """Obtener todos los mensajes"""
        return self._data_store["messages"].copy()
    
    def add_message(self, message: str) -> bool:
        """Agregar un nuevo mensaje"""
        if message:
            self._data_store["messages"].append(message)
            self._add_to_history("message_added", {"message": message})
            return True
        return False
    
    def get_counter(self) -> int:
        """Obtener el valor del contador"""
        return self._data_store["counter"]
    
    def increment_counter(self) -> int:
        """Incrementar el contador"""
        self._data_store["counter"] += 1
        self._add_to_history("counter_incremented", {"new_value": self._data_store["counter"]})
        return self._data_store["counter"]
    
    def reset_counter(self) -> int:
        """Reiniciar el contador"""
        old_value = self._data_store["counter"]
        self._data_store["counter"] = 0
        self._add_to_history("counter_reset", {"old_value": old_value})
        return 0
    
    def process_text(self, text: str, image_base64: str = None) -> Dict[str, Any]:
        """Procesar texto y devolver resultado"""
        if not text:
            return {"error": "Texto vacío"}
        
        # Lógica de procesamiento (ejemplo)
        processed = {
            "original": text,
            "processed": text.upper(),
            "length": len(text),
            "word_count": len(text.split()),
            "timestamp": datetime.now().isoformat(),
            "image_received": image_base64 is not None
        }
        
        self._add_to_history("text_processed", processed)
        return processed
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de operaciones"""
        return self._data_store["history"].copy()
    
    def clear_history(self) -> bool:
        """Limpiar historial"""
        self._data_store["history"].clear()
        return True
    
    def _add_to_history(self, action: str, data: Dict[str, Any]) -> None:
        """Agregar entrada al historial"""
        entry = {
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self._data_store["history"].append(entry)
        
        # Mantener solo los últimos 100 registros
        if len(self._data_store["history"]) > 100:
            self._data_store["history"] = self._data_store["history"][-100:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la aplicación"""
        return {
            "total_messages": len(self._data_store["messages"]),
            "current_counter": self._data_store["counter"],
            "history_entries": len(self._data_store["history"]),
            "last_updated": datetime.now().isoformat()
        }

# Instancia global del modelo (en una aplicación real usarías una base de datos)
data_model = DataModel() 