#!/bin/bash

echo "🚀 Instalando dependencias para BASF RAG System v2.0"
echo "=================================================="

# Verificar Python
echo "📋 Verificando Python..."
python --version

# Verificar pip
echo "📋 Verificando pip..."
pip --version

# Actualizar pip
echo "🔄 Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias principales
echo "📦 Instalando dependencias principales..."

# Flask API Core
pip install Flask==2.3.3
pip install Flask-CORS==4.0.0
pip install Werkzeug==2.3.7

# Google Gemini AI
pip install google-generativeai==0.3.2
pip install python-dotenv==1.0.0

# LangChain
pip install langchain==0.0.350
pip install langchain-google-genai==0.0.6
pip install langchain-community==0.0.4

# Vector Databases
pip install faiss-cpu==1.7.4
# chromadb ya no es necesario - usando FAISS

# Document Processing
pip install PyPDF2==3.0.1
pip install python-docx==0.8.11
pip install python-magic==0.4.27
pip install pillow==10.0.1
pip install pytesseract==0.3.10
pip install opencv-python==4.8.1.78
pip install pdfplumber==0.9.0

# Embeddings and ML
pip install sentence-transformers==2.2.2
pip install tiktoken==0.5.1

# Utilities
pip install requests==2.31.0
pip install numpy==1.24.3

echo "✅ Instalación completada!"
echo ""
echo "🔧 Configuración necesaria:"
echo "1. Asegúrate de tener GOOGLE_API_KEY en tu archivo .env"
echo "2. Ejecuta: python app.py"
echo "3. API disponible en: http://localhost:5001"
echo ""
echo "📚 Endpoints disponibles:"
echo "   • FAISS RAG: /api/rag-faiss/"
# echo "   • ChromaDB RAG: /api/rag/" - Ya no disponible
echo "   • Gemini AI: /api/gemini/"
echo ""
echo "📖 Ejemplo de uso:"
echo "   curl -X POST http://localhost:5001/api/rag-faiss/ingest \\"
echo "     -F 'files=@documento.pdf' \\"
echo "     -F 'title=Mi Documento' \\"
echo "     -F 'author=BASF'"
echo ""
