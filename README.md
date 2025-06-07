# 🚀 Web App MVC - Flask + Gradio

Una aplicación web completa usando arquitectura **Model-View-Controller (MVC)** con Flask como backend API y Gradio como interfaz de usuario.

## 📋 Características

- 🏗️ **Arquitectura MVC**: Separación clara de responsabilidades
- 🌐 **API REST**: Endpoints Flask completamente funcionales
- 🎨 **Interfaz Moderna**: UI interactiva con Gradio
- 📊 **Gestión de Datos**: Sistema completo de almacenamiento
- 📈 **Estadísticas**: Monitoreo en tiempo real
- 📋 **Historial**: Registro de todas las operaciones

## 🏗️ Estructura del Proyecto

```
ucuneurons/
├── app/
│   ├── __init__.py                 # Factory de la aplicación Flask
│   ├── config/
│   │   └── config.py              # Configuraciones de la app
│   ├── models/
│   │   └── data_model.py          # Modelo de datos (M)
│   ├── views/
│   │   └── gradio_interface.py    # Interfaz Gradio (V)
│   ├── controllers/
│   │   ├── main_controller.py     # Controlador principal (C)
│   │   └── api_controller.py      # Controlador API (C)
│   ├── static/                    # Archivos estáticos
│   └── templates/                 # Templates HTML
├── run.py                         # Ejecutar app completa
├── run_flask_only.py             # Solo Flask API
├── run_gradio_only.py            # Solo Gradio UI
├── requirements.txt              # Dependencias
└── README.md                     # Este archivo
```

## 🛠️ Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <tu-repositorio>
   cd ucuneurons
   ```

2. **Crear entorno virtual**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Uso

### Ejecutar Aplicación Completa
```bash
python run.py
```
- 🌐 **Flask API**: http://localhost:5000
- 🎨 **Gradio UI**: http://localhost:7860

### Ejecutar Solo Backend (Flask)
```bash
python run_flask_only.py
```
- Solo la API REST en http://localhost:5000

### Ejecutar Solo Frontend (Gradio)
```bash
python run_gradio_only.py
```
- Solo la interfaz en http://localhost:7860
- ⚠️ **Requiere** que Flask esté corriendo

## 🌐 Endpoints API

### Principales
- `GET /` - Información de la aplicación
- `GET /health` - Estado de salud
- `GET /info` - Información técnica

### API Endpoints
- `GET /api/` - Documentación de la API
- `GET|POST /api/data` - Gestión de datos
- `POST /api/process` - Procesamiento de texto
- `GET|POST|DELETE /api/counter` - Gestión de contador
- `GET /api/stats` - Estadísticas
- `GET|DELETE /api/history` - Historial de operaciones

### Ejemplos de Uso

**Procesar texto**:
```bash
curl -X POST http://localhost:5000/api/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Hola Mundo"}'
```

**Obtener estadísticas**:
```bash
curl http://localhost:5000/api/stats
```

**Incrementar contador**:
```bash
curl -X POST http://localhost:5000/api/counter
```

## 🎨 Interfaz Gradio

La interfaz incluye las siguientes pestañas:

1. **📝 Procesador de Texto**: Procesa texto usando la API
2. **🔢 Contador**: Gestiona un contador global
3. **💾 Datos**: Almacena y gestiona mensajes
4. **📊 Estadísticas**: Muestra métricas de la aplicación
5. **📋 Historial**: Registro de todas las operaciones

## ⚙️ Configuración

Puedes personalizar la configuración usando variables de entorno:

```bash
export FLASK_DEBUG=True
export API_PORT=5000
export GRADIO_PORT=7860
export API_HOST=0.0.0.0
export GRADIO_HOST=0.0.0.0
```

## 🏗️ Arquitectura MVC

### Model (Modelo)
- **`data_model.py`**: Gestiona toda la lógica de datos
- Operaciones CRUD
- Validación de datos
- Historial de operaciones

### View (Vista)
- **`gradio_interface.py`**: Interfaz de usuario interactiva
- Comunicación con API via HTTP
- Manejo de estados de UI
- Feedback visual al usuario

### Controller (Controlador)
- **`main_controller.py`**: Rutas principales y salud
- **`api_controller.py`**: Endpoints de la API REST
- Lógica de negocio
- Validación de requests
- Manejo de errores

## 🔧 Desarrollo

### Agregar Nuevos Endpoints
1. Modificar `app/controllers/api_controller.py`
2. Actualizar el modelo si es necesario
3. Agregar funcionalidad en Gradio si se requiere

### Personalizar la UI
1. Modificar `app/views/gradio_interface.py`
2. Agregar nuevas pestañas o componentes
3. Conectar con nuevos endpoints

### Configuraciones
1. Editar `app/config/config.py`
2. Agregar nuevas variables de entorno
3. Actualizar configuraciones por ambiente

## 📦 Dependencias

- **Flask**: Framework web backend
- **Flask-CORS**: Soporte para CORS
- **Gradio**: Interfaz de usuario interactiva
- **Requests**: Cliente HTTP para comunicación

## 🤝 Contribuir

1. Fork del proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request


## 🆘 Soporte

Si tienes problemas o preguntas:

1. Revisa que todas las dependencias estén instaladas
2. Verifica que los puertos 5000 y 7860 estén disponibles
3. Asegúrate de estar en el entorno virtual correcto
4. Revisa los logs de la consola para errores específicos

---

**¡Desarrollado con ❤️ usando Flask y Gradio!** 