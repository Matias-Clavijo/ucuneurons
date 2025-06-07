# 🏗️ Guía de Integración - Hackathon Risk Assessment

## 📋 Resumen del Orquestador

El **Orquestador Principal** (`app/controllers/main_flow_controller.py`) ya está implementado y coordinará todo el flujo de evaluación de riesgos:

```
Descripción inicial → Chatbot Expert → RAG → Cálculo → Reporte Final
```

## 🎯 Endpoints del Orquestador

### 1. Evaluación Completa
```bash
POST /evaluate-risk
{
  "prompt": "Descripción del proceso industrial..."
}
```

### 2. Evaluación Interactiva
```bash
POST /evaluate-risk/interactive
POST /evaluate-risk/{eval_id}/continue
GET  /evaluate-risk/{eval_id}/status
```

---

## 🤖 MÓDULO 1: Chatbot de Recopilación (✅ COMPLETO)

**Responsable:** Tu código actual
**Estado:** ✅ **FUNCIONANDO**

### Funcionalidad
- Recopila datos industriales mediante conversación inteligente
- **🆕 Analiza fotos del lugar de trabajo, equipos y operadores**
- Genera JSON estructurado con todos los datos necesarios + descripciones de fotos
- Funciona como microservicio independiente

### API Endpoints
```bash
POST /risk-chat/start                         # Crear sesión
POST /risk-chat/{session_id}/message          # Enviar mensaje
POST /risk-chat/{session_id}/analyze-image    # 🆕 Analizar foto
GET  /risk-chat/{session_id}/status           # Estado de sesión
```

### Salida Final
```json
{
  "status": "COMPLETO",
  "datos_tarea": {
    "quimicos_involucrados": ["ácido sulfúrico"],
    "proceso_detallado": "...",
    "contexto_fisico": {
      "ubicacion_pais": "España",
      "temperatura_trabajo": "20°C",
      "ventilacion_tipo": "general"
    },
    "contexto_temporal": {
      "duracion_exposicion": "15 min",
      "frecuencia_operacion": "2/día"
    },
    "cantidades_volumenes": "50 kg",
    "descripciones_fotos": [
      {
        "tipo": "lugar_trabajo",
        "descripcion": "Nave industrial con ventilación general, equipos de transferencia visibles"
      },
      {
        "tipo": "equipamiento_operadores",
        "descripcion": "Operadores con EPIs completos, duchas de emergencia disponibles"
      }
    ]
  }
}
```

---

## 📚 MÓDULO 2: RAG (🔄 PENDIENTE DE INTEGRACIÓN)

**Responsable:** Compañero del equipo
**Estado:** 🔄 **ESPERANDO IMPLEMENTACIÓN**

### Función Esperada
Enriquecer datos con información externa:
- Fichas de Datos de Seguridad (FDS)
- Normativas por país
- Datos de peligrosidad

### Integración Requerida

#### Endpoint a Implementar
```bash
POST /rag/enrich
Content-Type: application/json

{
  "quimicos": ["ácido sulfúrico", "acetona"],
  "pais": "España"
}
```

#### Respuesta Esperada
```json
{
  "status": "success",
  "datos_enriquecidos": {
    "fds_encontradas": 2,
    "quimicos_data": {
      "ácido sulfúrico": {
        "cas": "7664-93-9",
        "peligros": ["Corrosivo", "Tóxico"],
        "medidas_seguridad": ["Ventilación", "EPIs"],
        "limites_exposicion": "1 mg/m³"
      }
    },
    "legislacion_pais": "RD 374/2001 España",
    "recomendaciones_adicionales": ["..."]
  }
}
```

#### Código de Integración (Ya implementado en orquestador)
```python
# En main_flow_controller.py línea ~120
def _call_rag_module(quimicos, pais, eval_id):
    # TODO: Reemplazar esta simulación con tu código real:
    rag_response = requests.post(f'{INTERNAL_BASE_URL}/rag/enrich', json={
        "quimicos": quimicos,
        "pais": pais
    })
    return rag_response.json()
```

---

## 🧮 MÓDULO 3: Motor de Cálculo (🔄 PENDIENTE DE INTEGRACIÓN)

**Responsable:** Otro miembro del equipo
**Estado:** 🔄 **ESPERANDO IMPLEMENTACIÓN**

### Función Esperada
Calcular nivel de riesgo basado en:
- Datos recopilados por el chatbot
- Datos enriquecidos por RAG
- Algoritmos de evaluación de riesgos

### Integración Requerida

#### Opción A: Endpoint REST
```bash
POST /calculation/risk-assessment
{
  "datos_tarea": { /* Salida del chatbot */ },
  "datos_enriquecidos": { /* Salida del RAG */ }
}
```

#### Opción B: Función Python (Recomendada)
```python
# Crear: app/services/calculation_engine.py
def calcular_riesgo(datos_tarea, datos_enriquecidos):
    """
    Calcular riesgo industrial
    
    Returns:
    {
        "nivel_riesgo": "ALTO|MEDIO|BAJO",
        "puntuacion": 0-100,
        "factores_criticos": ["Factor1", "Factor2"],
        "recomendaciones": ["Acción1", "Acción2"],
        "metadatos": {"algoritmo": "v1.0", "confianza": 0.85}
    }
    """
    # Tu algoritmo aquí
    pass
```

#### Código de Integración (Ya implementado en orquestador)
```python
# En main_flow_controller.py línea ~140
def _call_calculation_engine(datos_tarea, datos_enriquecidos, eval_id):
    # TODO: Reemplazar esta simulación:
    from app.services.calculation_engine import calcular_riesgo
    return calcular_riesgo(datos_tarea, datos_enriquecidos)
```

---

## 📄 MÓDULO 4: Generación de Reportes (🔄 OPCIONAL)

**Responsable:** Cualquier miembro del equipo
**Estado:** 🔄 **OPCIONAL PARA HACKATHON**

### Función Esperada
Generar reporte final con:
- Resumen ejecutivo
- Datos recopilados
- Nivel de riesgo calculado
- Recomendaciones específicas
- PDF descargable

---

## 🚀 Instrucciones de Integración

### Para el Módulo RAG:
1. Implementa el endpoint `POST /rag/enrich`
2. Registra tu blueprint en `app/__init__.py`
3. El orquestador ya está preparado para llamarlo

### Para el Módulo de Cálculo:
1. **Opción fácil:** Crea `app/services/calculation_engine.py` con la función `calcular_riesgo()`
2. **Opción REST:** Implementa endpoint y modifica `_call_calculation_engine()`

### Para Probar la Integración:
```bash
# 1. Ejecutar Flask
python run_flask_only.py

# 2. Probar orquestador
python test_orchestrator.py

# 3. Probar endpoint completo
curl -X POST http://localhost:5001/evaluate-risk \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Evaluar uso de acetona en España, 1L por día"}'
```

---

## 🎯 Checklist de Integración

### ✅ Módulo Chatbot
- [x] Implementado y funcionando
- [x] Integrado en orquestador
- [x] Probado con múltiples casos

### 🔄 Módulo RAG
- [ ] Implementar endpoint `/rag/enrich`
- [ ] Conectar con bases de datos de FDS
- [ ] Integrar normativas por país
- [ ] Probar con orquestador

### 🔄 Módulo Cálculo
- [ ] Definir algoritmia de evaluación
- [ ] Implementar función/endpoint
- [ ] Integrar con orquestador
- [ ] Validar resultados

### 🔄 Módulo Reportes (Opcional)
- [ ] Plantillas de reporte
- [ ] Generación de PDF
- [ ] Integración final

---

## 🎉 Estado Actual

```
✅ Orquestador Principal - FUNCIONANDO
✅ Módulo Chatbot - FUNCIONANDO  
🔄 Módulo RAG - ESPERANDO INTEGRACIÓN
🔄 Módulo Cálculo - ESPERANDO INTEGRACIÓN
🔄 Módulo Reportes - OPCIONAL

🚀 LISTO PARA HACKATHON: 50%
```

## 📞 Coordinación del Equipo

**Tu rol:** ✅ Módulo de Recopilación + Orquestador Principal (COMPLETO)

**Siguiente:** Los compañeros pueden empezar a implementar sus módulos de forma paralela, todos los puntos de integración están definidos y preparados. 