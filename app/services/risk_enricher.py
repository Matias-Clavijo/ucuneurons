"""
Paso 2: Módulo de Enriquecimiento con "Multi-Consulta Dirigida"

Este módulo implementa una estrategia de búsqueda exhaustiva y metódica que:
1. Define objetivos de datos específicos
2. Itera por cada químico y cada objetivo
3. Consolida contexto de alta calidad
4. Usa LLM una sola vez al final para estructurar

Autor: Sistema UCU Neurons - Módulo RAG Avanzado
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.models.gemini_model import gemini_model
# TODO: Cuando tu compañero termine el cliente ChromaDB, importar así:
# from app.services.vector_db_client import vector_db_client


class RiskDataEnricher:
    """
    Enriquecedor de datos de riesgo con estrategia Multi-Consulta Dirigida.
    
    Esta clase orquesta un proceso de investigación metódico que garantiza
    obtener toda la información crítica de todas las fuentes pertinentes.
    """
    
    # 1. OBJETIVOS DE DATOS ESPECÍFICOS
    # La clave es el campo final en nuestro JSON, el valor es el texto a buscar
    OBJETIVOS_DATOS_FDS = {
        "vla_mg_m3": "Valor Límite Ambiental Exposición Diaria VLA-ED en mg/m3",
        "vla_ppm": "Valor Límite Ambiental Exposición Diaria VLA-ED en ppm",
        "presion_vapor_hpa": "Presión de vapor en hPa a 20°C",
        "punto_ebullicion_c": "Punto de ebullición o punto inicial de ebullición en °C",
        "punto_fusion_c": "Punto de fusión o punto de congelación en °C",
        "densidad_relativa": "Densidad relativa del vapor respecto al aire",
        "frases_h": "Indicaciones de peligro Frases H",
        "frases_p": "Consejos de prudencia Frases P",
        "epp_manos": "Protección de las manos, guantes recomendados, material de los guantes",
        "epp_respiratoria": "Protección respiratoria, tipo de filtro, equipo de respiración",
        "epp_ocular": "Protección de los ojos/la cara, gafas de seguridad",
        "ventilacion_requerida": "Medidas técnicas apropiadas, ventilación, extracción localizada",
        "incompatibilidades": "Materiales a evitar, productos incompatibles",
        "productos_descomposicion": "Productos de descomposición peligrosos",
        "condiciones_almacenamiento": "Condiciones de almacenamiento seguro"
    }
    
    # 2. OBJETIVOS DE BÚSQUEDA LEGAL
    OBJETIVOS_DATOS_LEGALES = {
        "limites_exposicion_ocupacional": "límites de exposición ocupacional",
        "requisitos_ventilacion": "requisitos de ventilación industrial",
        "obligaciones_epp": "obligaciones de equipos de protección personal",
        "restricciones_almacenamiento": "restricciones de almacenamiento de químicos",
        "requisitos_notificacion": "requisitos de notificación autoridades",
        "evaluacion_riesgo_obligatoria": "evaluación de riesgo obligatoria"
    }

    def __init__(self, model=None, db_client=None):
        """
        Inicializar el enriquecedor.
        
        Args:
            model: Modelo Gemini (por defecto usa gemini_model global)
            db_client: Cliente de base de datos vectorial (ChromaDB)
        """
        self.model = model or gemini_model
        self.db_client = db_client  # TODO: Conectar cuando esté disponible
        self.debug_mode = True  # Para logging detallado
    
    def enrich_task_data(self, task_data: dict) -> dict:
        """
        ORQUESTADOR PRINCIPAL del proceso de enriquecimiento.
        
        Recibe el JSON del Paso 1 y entrega un JSON Enriquecido usando
        la estrategia de Multi-Consulta Dirigida.
        
        Args:
            task_data: JSON con datos de la tarea del chatbot
            
        Returns:
            dict: JSON enriquecido con toda la información técnica
        """
        try:
            # Extraer datos clave de la tarea
            quimicos = task_data.get('datos_tarea', {}).get('quimicos_involucrados', [])
            pais = task_data.get('datos_tarea', {}).get('contexto_fisico', {}).get('ubicacion_pais', 'España')
            
            if not quimicos:
                return {
                    "status": "error",
                    "message": "No se encontraron químicos en los datos de la tarea",
                    "timestamp": datetime.now().isoformat()
                }
            
            if self.debug_mode:
                print(f"🔍 INICIANDO ENRIQUECIMIENTO para {len(quimicos)} químicos: {quimicos}")
            
            # FASE 1: Recopilación exhaustiva de contexto
            contexto_consolidado = self._recopilar_contexto_completo(quimicos, pais)
            
            # FASE 2: Síntesis con LLM
            datos_enriquecidos = self._sintetizar_informacion(
                contexto_consolidado, 
                task_data, 
                quimicos, 
                pais
            )
            
            return {
                "status": "success",
                "datos_originales": task_data,
                "datos_enriquecidos": datos_enriquecidos,
                "quimicos_procesados": quimicos,
                "pais": pais,
                "timestamp": datetime.now().isoformat(),
                "debug_contexto_length": len(contexto_consolidado) if self.debug_mode else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error en enriquecimiento: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _recopilar_contexto_completo(self, quimicos: List[str], pais: str) -> str:
        """
        FASE 1: Recopilación exhaustiva usando Multi-Consulta Dirigida.
        
        Para cada químico, busca específicamente cada objetivo de dato.
        """
        contexto_consolidado = ""
        
        # PASO A: Búsqueda por químico y objetivo de dato FDS
        for quimico in quimicos:
            contexto_consolidado += f"\n{'='*80}\n"
            contexto_consolidado += f"INICIO CONTEXTO FDS PARA: {quimico.upper()}\n"
            contexto_consolidado += f"{'='*80}\n"
            
            for campo, consulta in self.OBJETIVOS_DATOS_FDS.items():
                if self.debug_mode:
                    print(f"  🔎 Buscando '{campo}' para '{quimico}'...")
                
                # Simular búsqueda en DB vectorial (cuando esté disponible)
                contexto_campo = self._buscar_informacion_especifica(
                    quimico, consulta, "FDS"
                )
                
                contexto_consolidado += f"\n--- {campo.upper().replace('_', ' ')} ---\n"
                contexto_consolidado += f"Consulta: {consulta}\n"
                contexto_consolidado += f"Resultado: {contexto_campo}\n"
            
            contexto_consolidado += f"\n{'='*80}\n"
            contexto_consolidado += f"FIN CONTEXTO FDS PARA: {quimico.upper()}\n"
            contexto_consolidado += f"{'='*80}\n"
        
        # PASO B: Búsqueda de información legal específica
        contexto_consolidado += f"\n{'='*80}\n"
        contexto_consolidado += f"INICIO CONTEXTO LEGAL PARA: {pais.upper()}\n"
        contexto_consolidado += f"{'='*80}\n"
        
        for campo_legal, consulta_legal in self.OBJETIVOS_DATOS_LEGALES.items():
            if self.debug_mode:
                print(f"  ⚖️ Buscando '{campo_legal}' para '{pais}'...")
            
            contexto_legal = self._buscar_informacion_legal(
                quimicos, consulta_legal, pais
            )
            
            contexto_consolidado += f"\n--- {campo_legal.upper().replace('_', ' ')} ---\n"
            contexto_consolidado += f"Consulta: {consulta_legal}\n"
            contexto_consolidado += f"Resultado: {contexto_legal}\n"
        
        contexto_consolidado += f"\n{'='*80}\n"
        contexto_consolidado += f"FIN CONTEXTO LEGAL\n"
        contexto_consolidado += f"{'='*80}\n"
        
        return contexto_consolidado
    
    def _buscar_informacion_especifica(self, quimico: str, consulta: str, tipo_doc: str) -> str:
        """
        Búsqueda específica en base de datos vectorial.
        
        TODO: Reemplazar con llamada real al vector_db_client cuando esté disponible.
        """
        if self.db_client:
            try:
                resultados = self.db_client.search(
                    query=f"{consulta} para {quimico}",
                    n_results=2,
                    filter={
                        "tipo_archivo": tipo_doc,
                        "quimico": quimico.lower()
                    }
                )
                
                if resultados.get("status") == "success" and resultados.get("documents"):
                    return "\n".join(resultados["documents"])
                else:
                    return f"No se encontró información específica en {tipo_doc} para {quimico}"
                    
            except Exception as e:
                return f"Error en búsqueda: {str(e)}"
        else:
            # SIMULACIÓN: Respuesta mock mientras se implementa ChromaDB
            return f"[SIMULADO] Información de {consulta} para {quimico}"
    
    def _buscar_informacion_legal(self, quimicos: List[str], consulta: str, pais: str) -> str:
        """
        Búsqueda específica de información legal.
        """
        if self.db_client:
            try:
                resultados = self.db_client.search(
                    query=f"{consulta} {' '.join(quimicos)} {pais}",
                    n_results=3,
                    filter={
                        "tipo_archivo": "legal",
                        "pais": pais.lower()
                    }
                )
                
                if resultados.get("status") == "success" and resultados.get("documents"):
                    return "\n".join(resultados["documents"])
                else:
                    return f"No se encontró información legal específica para {pais}"
                    
            except Exception as e:
                return f"Error en búsqueda legal: {str(e)}"
        else:
            # SIMULACIÓN: Respuesta mock
            return f"[SIMULADO] Información legal de {consulta} para {pais}"
    
    def _sintetizar_informacion(self, contexto: str, task_data: dict, quimicos: List[str], pais: str) -> dict:
        """
        FASE 2: Síntesis final con LLM usando todo el contexto recopilado.
        
        Aquí es donde usamos el LLM UNA SOLA VEZ con contexto de alta calidad.
        """
        synthesis_prompt = self._build_synthesis_prompt(contexto, task_data, quimicos, pais)
        
        if self.debug_mode:
            print(f"🧠 SÍNTESIS FINAL con LLM...")
            print(f"   Longitud del contexto: {len(contexto)} caracteres")
        
        # Llamada única al LLM con todo el contexto
        synthesis_result = self.model.generate_text(
            prompt=synthesis_prompt, 
            temperature=0.1  # Precisión máxima
        )
        
        if synthesis_result["status"] == "error":
            return {
                "error": "Fallo en síntesis LLM",
                "details": synthesis_result["message"]
            }
        
        # Parsear JSON estructurado
        try:
            datos_estructurados = json.loads(synthesis_result["text"])
            return datos_estructurados
        except json.JSONDecodeError as e:
            # Fallback: devolver respuesta raw si el JSON no es válido
            return {
                "error": "JSON inválido del LLM",
                "raw_response": synthesis_result["text"],
                "parse_error": str(e)
            }
    
    def _build_synthesis_prompt(self, context: str, task_data: dict, quimicos: List[str], pais: str) -> str:
        """
        Construir el prompt final de síntesis.
        
        Este prompt es crítico: debe extraer y estructurar perfectamente
        toda la información recopilada.
        """
        # Campos JSON que esperamos
        campos_fds = list(self.OBJETIVOS_DATOS_FDS.keys())
        campos_legales = list(self.OBJETIVOS_DATOS_LEGALES.keys())
        
        return f"""# ROL Y MISIÓN
Eres un Higienista Industrial experto especializado en evaluación de riesgos químicos.
Tu única misión es extraer datos técnicos precisos de la documentación consolidada y estructurarlos en JSON.

# TAREA ORIGINAL
Químicos involucrados: {', '.join(quimicos)}
País: {pais}
Actividad: {task_data.get('datos_tarea', {}).get('actividad_realizada', 'No especificada')}

# DOCUMENTACIÓN CONSOLIDADA DE REFERENCIA
{context}

# INSTRUCCIONES CRÍTICAS
1. Analiza exhaustivamente la documentación consolidada
2. Extrae TODOS los datos técnicos disponibles para cada químico
3. Si un dato no se encuentra, usa explícitamente `null`
4. Si encuentras datos para múltiples químicos, estructura como array de objetos
5. Prioriza datos numéricos exactos sobre rangos o descripciones vagas
6. DEVUELVE ÚNICAMENTE el objeto JSON, sin explicaciones adicionales

# FORMATO JSON REQUERIDO (ESTRICTO)
{{
    "quimicos_datos": [
        {{
            "nombre_quimico": "string",
            "vla_mg_m3": number_or_null,
            "vla_ppm": number_or_null,
            "presion_vapor_hpa": number_or_null,
            "punto_ebullicion_c": number_or_null,
            "punto_fusion_c": number_or_null,
            "densidad_relativa": number_or_null,
            "frases_h": ["H200", "H300"] or null,
            "frases_p": ["P200", "P300"] or null,
            "epp_manos": "string_or_null",
            "epp_respiratoria": "string_or_null",
            "epp_ocular": "string_or_null",
            "ventilacion_requerida": "string_or_null",
            "incompatibilidades": ["sustancia1", "sustancia2"] or null,
            "productos_descomposicion": ["producto1", "producto2"] or null,
            "condiciones_almacenamiento": "string_or_null"
        }}
    ],
    "contexto_legal": {{
        "pais": "{pais}",
        "limites_exposicion_ocupacional": "string_or_null",
        "requisitos_ventilacion": "string_or_null",
        "obligaciones_epp": "string_or_null",
        "restricciones_almacenamiento": "string_or_null",
        "requisitos_notificacion": "string_or_null",
        "evaluacion_riesgo_obligatoria": "string_or_null"
    }},
    "resumen_criticidad": {{
        "nivel_riesgo_general": "ALTO|MEDIO|BAJO",
        "quimicos_mas_peligrosos": ["quimico1", "quimico2"],
        "medidas_criticas_inmediatas": ["medida1", "medida2"]
    }}
}}"""

    def get_status(self) -> dict:
        """Estado del enriquecedor"""
        return {
            "service": "RiskDataEnricher",
            "version": "2.0 - Multi-Consulta Dirigida",
            "model_available": self.model.is_available(),
            "db_client_available": bool(self.db_client),
            "objetivos_fds": len(self.OBJETIVOS_DATOS_FDS),
            "objetivos_legales": len(self.OBJETIVOS_DATOS_LEGALES),
            "debug_mode": self.debug_mode,
            "timestamp": datetime.now().isoformat()
        }


# Instancia global del enriquecedor
risk_enricher = RiskDataEnricher() 