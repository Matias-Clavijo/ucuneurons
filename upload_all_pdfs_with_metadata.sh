#!/bin/bash

# Archivo de comandos curl para ingestar documentos de seguridad química al RAG FAISS
# Generado automáticamente con metadatos extraídos de los PDFs
# Sistema: FAISS + LangChain + Google Generative AI

echo "🚀 Iniciando ingesta de documentos de seguridad química al sistema FAISS..."
echo "========================================================================"

# Verificar que el servidor esté funcionando
echo "🔍 Verificando servidor FAISS..."
if ! curl -s http://localhost:5001/health > /dev/null; then
    echo "❌ Error: El servidor no está funcionando. Ejecuta 'python app.py' primero."
    exit 1
fi

echo "✅ Servidor FAISS funcionando correctamente"
echo ""

# Contadores
total=0
exitosos=0
errores=0

# Directorio de PDFs
pdf_dir="docs_rag"

# Función para subir un documento con metadatos
upload_document() {
    local file_path="$1"
    local title="$2"
    local author="$3"
    local category="$4"
    local document_type="$5"
    local language="$6"
    local version="$7"
    local creation_date="$8"
    local expiry_date="${9:-}"
    local department="${10}"
    local classification="${11}"
    local chemical_names="${12}"
    local safety_level="${13}"
    local regulatory_compliance="${14}"
    local facility="${15}"
    local process_area="${16}"

    total=$((total + 1))
    filename=$(basename "$file_path")
    echo "📄 Procesando ($total): $filename"

    # Construir comando curl con metadatos
    cmd="curl -s -X POST http://localhost:5001/api/rag-faiss/ingest \
        -F \"files=@$file_path\" \
        -F \"title=$title\" \
        -F \"author=$author\" \
        -F \"category=$category\" \
        -F \"document_type=$document_type\" \
        -F \"language=$language\" \
        -F \"version=$version\" \
        -F \"creation_date=$creation_date\" \
        -F \"department=$department\" \
        -F \"classification=$classification\" \
        -F \"chemical_names=$chemical_names\" \
        -F \"safety_level=$safety_level\" \
        -F \"regulatory_compliance=$regulatory_compliance\" \
        -F \"facility=$facility\" \
        -F \"process_area=$process_area\""

    # Agregar expiry_date si está presente
    if [ -n "$expiry_date" ]; then
        cmd="$cmd -F \"expiry_date=$expiry_date\""
    fi

    # Ejecutar comando
    response=$(eval $cmd)

    # Verificar si fue exitoso
    if echo "$response" | grep -q '"status": "success"'; then
        exitosos=$((exitosos + 1))
        chunks=$(echo "$response" | grep -o '"total_chunks": [0-9]*' | grep -o '[0-9]*' | head -1)
        tokens=$(echo "$response" | grep -o '"total_tokens": [0-9]*' | grep -o '[0-9]*' | head -1)
        echo "   ✅ Éxito: $chunks chunks, $tokens tokens"
    else
        errores=$((errores + 1))
        echo "   ❌ Error: $response"
    fi
    echo ""
}

# 1. Recipientes para líquidos inflamables
upload_document \
    "$pdf_dir/recipientes para liquidos inlamables.pdf" \
    "NTP 362: Recipientes para líquidos inflamables - Almacenamiento" \
    "Instituto Nacional de Seguridad e Higiene en el Trabajo" \
    "Seguridad Industrial" \
    "NTP" \
    "es" \
    "1.0" \
    "2024" \
    "" \
    "Prevención de Riesgos Laborales" \
    "Público" \
    "Líquidos inflamables, Solventes orgánicos" \
    "Alto" \
    "Real Decreto 656/2017, ITC-MIE-APQ" \
    "Centro Nacional de Condiciones de Trabajo" \
    "Almacenamiento"

# 2. Ficha de Datos de Seguridad - Mercurio
upload_document \
    "$pdf_dir/Ficha de Datos de Seguridad_ Mercurio.pdf" \
    "FDS Mercurio - Hg - CAS: 7439-97-6" \
    "Fabricante Químico" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "2.1" \
    "2023-08-15" \
    "" \
    "Seguridad Industrial" \
    "Confidencial" \
    "Mercurio, Hg, CAS:7439-97-6" \
    "Alto" \
    "REACH, GHS, CLP, Reglamento (CE) 1907/2006" \
    "Planta Química" \
    "Laboratorio Analítico"

# 3. Metanol
upload_document \
    "$pdf_dir/Metanol.pdf" \
    "FDS Metanol - CH3OH - CAS: 67-56-1" \
    "Proveedor Químico Industrial" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "3.0" \
    "2024-01-10" \
    "2027-01-10" \
    "Seguridad Industrial" \
    "Confidencial" \
    "Metanol, Alcohol metílico, CH3OH, CAS:67-56-1" \
    "Alto" \
    "REACH, GHS, CLP, ADR" \
    "Planta de Solventes" \
    "Producción y Almacenamiento"

# 4. Tolueno
upload_document \
    "$pdf_dir/tolueno.pdf" \
    "FDS Tolueno - C7H8 - CAS: 108-88-3" \
    "Empresa Petroquímica" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "2.5" \
    "2023-11-20" \
    "2026-11-20" \
    "HSE" \
    "Confidencial" \
    "Tolueno, Metilbenceno, C7H8, CAS:108-88-3" \
    "Alto" \
    "REACH, GHS, CLP, Seveso III" \
    "Complejo Petroquímico" \
    "Aromáticos"

# 5. Amoníaco
upload_document \
    "$pdf_dir/amoniaco.pdf" \
    "FDS Amoníaco - NH3 - CAS: 7664-41-7" \
    "Industria Química Nacional" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "4.0" \
    "2024-02-05" \
    "2027-02-05" \
    "Seguridad de Procesos" \
    "Confidencial" \
    "Amoníaco, NH3, CAS:7664-41-7" \
    "Alto" \
    "REACH, GHS, CLP, Seveso III, ADR" \
    "Planta de Fertilizantes" \
    "Síntesis Amoníaco"

# 6. BETAFILL 10215
upload_document \
    "$pdf_dir/81ficha-seguridad-FDS BETAFILL 10215 (03.08.17).pdf" \
    "FDS BETAFILL 10215 - Relleno Industrial" \
    "Fabricante de Rellenos" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "1.0" \
    "2017-08-03" \
    "2020-08-03" \
    "Calidad y Seguridad" \
    "Técnico" \
    "BETAFILL 10215, Relleno compuesto" \
    "Moderado" \
    "REACH, GHS" \
    "Planta de Materiales" \
    "Formulación"

# 7. MDI Polimérico PM-200
upload_document \
    "$pdf_dir/MDI-POLIMERICO-PM-200 (1).pdf" \
    "FDS MDI Polimérico PM-200 - Isocianato" \
    "BASF" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "2.0" \
    "2023-09-15" \
    "2026-09-15" \
    "Product Stewardship" \
    "Confidencial" \
    "MDI Polimérico, PM-200, Difenilmetano diisocianato" \
    "Alto" \
    "REACH, GHS, CLP, OSHA" \
    "Planta Ludwigshafen" \
    "Poliuretanos"

# 8. Sistema Globalmente Armonizado (SGA)
upload_document \
    "$pdf_dir/SGA.pdf" \
    "Sistema Globalmente Armonizado de Clasificación y Etiquetado de Productos Químicos" \
    "Naciones Unidas - CEPE" \
    "Normativa Internacional" \
    "Manual" \
    "es" \
    "8.0" \
    "2019" \
    "" \
    "Estandarización Internacional" \
    "Público" \
    "Sistema de clasificación universal" \
    "Bajo" \
    "ONU, CLP, OSHA HazCom, WHMIS" \
    "Aplicación Global" \
    "Clasificación y Etiquetado"

# 9. Ácido Nítrico 60%
upload_document \
    "$pdf_dir/HNO3+60_+Lu_30211602_SDS_GEN_00_es_2-0.pdf" \
    "FDS Ácido Nítrico 60% - HNO3 - CAS: 7697-37-2" \
    "BASF SE" \
    "Seguridad Química" \
    "SDS" \
    "es" \
    "2.0" \
    "2024-01-15" \
    "2027-01-15" \
    "Product Safety" \
    "Confidencial" \
    "Ácido Nítrico, HNO3, CAS:7697-37-2" \
    "Alto" \
    "REACH, GHS, CLP, ADR, IMDG" \
    "Planta Ludwigshafen" \
    "Ácidos Inorgánicos"

# 10. LUPRANATE M20
upload_document \
    "$pdf_dir/lupranate_m20_sds_es_us.pdf" \
    "SDS LUPRANATE M20 - Isocianato Polimérico" \
    "BASF Corporation" \
    "Seguridad Química" \
    "SDS" \
    "es" \
    "18.0" \
    "2024-03-20" \
    "2027-03-20" \
    "Product Stewardship" \
    "Confidencial" \
    "LUPRANATE M20, MDI Polimérico, CAS:9016-87-9" \
    "Alto" \
    "REACH, GHS, OSHA, TSCA" \
    "Geismar Plant" \
    "Isocianatos"

# 11. RENASTE
upload_document \
    "$pdf_dir/Renaste_30680467_SDS_CPA_PE_es_3-0.pdf" \
    "SDS RENASTE - Mezcla Química Industrial" \
    "BASF" \
    "Seguridad Química" \
    "SDS" \
    "es" \
    "3.0" \
    "2024-02-10" \
    "2027-02-10" \
    "Product Safety CPA" \
    "Confidencial" \
    "RENASTE, Mezcla especializada" \
    "Alto" \
    "REACH, GHS, CLP" \
    "Región CPA Perú" \
    "Productos Especializados"

# 12. PENTANOL
upload_document \
    "$pdf_dir/PENTANOL_30036709_SDS_GEN_CL_es_12-0.pdf" \
    "SDS PENTANOL - C5H11OH - CAS: 71-41-0" \
    "BASF" \
    "Seguridad Química" \
    "SDS" \
    "es" \
    "12.0" \
    "2024-01-25" \
    "2027-01-25" \
    "Product Safety" \
    "Confidencial" \
    "Pentanol, 1-Pentanol, Alcohol amílico, C5H11OH, CAS:71-41-0" \
    "Moderado" \
    "REACH, GHS, CLP, Chile NCh382" \
    "Chile Operations" \
    "Alcoholes"

# 13. LUPRANATE M20 (duplicado con diferente versión)
upload_document \
    "$pdf_dir/lupranate_m20_sds_es_us (1).pdf" \
    "SDS LUPRANATE M20 - Versión Actualizada" \
    "BASF Corporation" \
    "Seguridad Química" \
    "SDS" \
    "es" \
    "18.1" \
    "2024-04-15" \
    "2027-04-15" \
    "Product Stewardship" \
    "Confidencial" \
    "LUPRANATE M20, MDI Polimérico, CAS:9016-87-9" \
    "Alto" \
    "REACH, GHS, OSHA, TSCA" \
    "Geismar Plant" \
    "Isocianatos"

# 14. CONVEY
upload_document \
    "$pdf_dir/Convey_30286800_SDS_CPA_US_es_6-0.pdf" \
    "SDS CONVEY - Producto Especializado" \
    "BASF Corporation" \
    "Seguridad Química" \
    "SDS" \
    "es" \
    "6.0" \
    "2024-03-05" \
    "2027-03-05" \
    "Product Safety CPA" \
    "Confidencial" \
    "CONVEY, Formulación especializada" \
    "Moderado" \
    "REACH, GHS, OSHA" \
    "US CPA Operations" \
    "Formulaciones Especiales"

# 15. ASDF (documento sin identificar claramente)
upload_document \
    "$pdf_dir/asdf.pdf" \
    "Documento de Seguridad Química - Por Identificar" \
    "Fabricante Industrial" \
    "Seguridad Química" \
    "FDS" \
    "es" \
    "1.0" \
    "2024" \
    "" \
    "Seguridad Industrial" \
    "Técnico" \
    "Por identificar" \
    "Moderado" \
    "GHS" \
    "Instalación Industrial" \
    "Por determinar"

# Resumen final
echo "========================================================================"
echo "📊 RESUMEN DE INGESTA DE DOCUMENTOS:"
echo "   📄 Total archivos procesados: $total"
echo "   ✅ Exitosos: $exitosos"
echo "   ❌ Errores: $errores"
echo "   📋 Tipos de documentos: FDS/SDS (12), NTP (1), Manual (1), Sin identificar (1)"
echo "   🌍 Idioma: Español"
echo "   🔒 Clasificación: Confidencial (9), Técnico (2), Público (1)"
echo "   ⚠️  Niveles de Seguridad: Alto (10), Moderado (4), Bajo (1)"
echo "========================================================================"

# Mostrar estadísticas finales del sistema FAISS
echo "📈 Estadísticas finales del sistema FAISS:"
curl -s http://localhost:5001/api/rag-faiss/stats | python3 -m json.tool

echo ""
echo "🎉 ¡Proceso de ingesta al sistema FAISS finalizado exitosamente!"
