#!/usr/bin/env python3
"""
Test script for the transcript processor functionality
"""

import asyncio
import json
import os
from datetime import datetime
from server.main import process_transcript_and_generate_sql

async def test_transcript_processor():
    """
    Test the transcript processor with a sample YouTube URL and prompt
    """
    
    # URL de ejemplo de YouTube
    youtube_url = "https://www.youtube.com/watch?v=Vmb1tqYqyII"
    
    # Prompt personalizado para el procesamiento
    custom_prompt = """
    Actúa como un procesador de transcripciones de video para una aplicación de aprendizaje de idiomas. Recibirás un objeto JSON que contiene una lista de clips con texto hablado en inglés y sus marcas de tiempo (`start`, `end`, `duration`).

    Tu tarea es:

    ### 🔄 1. Agrupar Clips
    Agrupa los clips en bloques de hasta **3 segmentos consecutivos**. Solo une clips adyacentes si forman una frase completa o una unidad de significado. El número máximo de clips por grupo es 3, pero pueden ser menos si la estructura del contenido lo requiere.

    ### ✍️ 2. Fusionar Campos
    - Funde los textos de los clips agrupados en un solo string en el campo `text`.
    - Calcula:
      - `start`: es el `start` del primer clip del grupo.
      - `end`: es el `end` del último clip del grupo.
      - `duration`: es la diferencia `end - start`.
    - Asegurate de hacer bien los calculos

    ### 🌍 3. Agregar Traducción
    Traduce el nuevo `text` al **español neutro**, cuidando que sea:
    - Natural y claro.
    - Correcto gramaticalmente.
    - Adaptado para estudiantes intermedios de inglés.

    Agrega un nuevo campo:  
    ```json
    "text_translate": "Traducción en español del campo text"
    ```

    ### 🧠 4. Extraer vocabulario por clip
    Para cada clip nuevo, incluye un nuevo campo llamado `"vocabulary"` que sea un array de objetos con las siguientes claves:

    - `"original_word"`: palabra o frase en inglés relevante para el aprendizaje.
    - `"translation"`: traducción al español.
    - `"notes"`: explicación opcional sobre uso, contexto, si es técnico, informal, phrasal verb, etc.

    Selecciona mas de un elemento del texto agrupado que sean útiles didácticamente. Prioriza:

    - Phrasal verbs
    - Términos técnicos
    - Verbos clave
    - Vocabulario avanzado o contextual

    ### 🧱 5. Mantén la Estructura
    La salida debe tener el mismo formato JSON que el original, pero con los textos fusionados, los campos start, end, duration recalculados, y un nuevo campo text_translate en cada entrada de transcript.

    Ejemplo de un elemento transformado:
{
  "transcript": [
    {
      "text": "This is the first sentence. This is the second sentence.",
      "start": 0.12,
      "end": 5.28,
      "duration": 5.159,
      "text_translate": "Esta es la primera oración. Esta es la segunda oración.",
      "vocabulary": [
        {
          "original_word": "phrasal verb o término",
          "translation": "traducción",
          "notes": "opcional"
        }
      ]
    },
    ...
  ],
  "video_id": "...",
  "url": "...",
  "language": "en"
}



Recibirás un JSON con esta forma:

{
  "transcript": [
    {"text": "...", "start": ..., "end": ..., "duration": ...},
    ...
  ],
  "video_id": "...",
  "url": "...",
  "language": "..."
}


📤 Output:
Devuelve un nuevo JSON con la misma estructura, pero con los clips agrupados, text fusionado, tiempo ajustado, y text_translate traducido al español.

NO agregues ningún texto adicional. Solo devuelve el JSON transformado.
    """
    
    try:
        print("🔄 Procesando transcripción de YouTube...")
        print(f"URL: {youtube_url}")
        print(f"Prompt: {custom_prompt[:100]}...")
        print("-" * 50)
        
        # Procesar la transcripción
        result = await process_transcript_and_generate_sql(youtube_url, custom_prompt)
        
        print("✅ Procesamiento completado exitosamente!")
        print("\n📊 Datos procesados:")
        print(json.dumps(result.processed_data, indent=2, ensure_ascii=False))
        
        print("\n🗄️ INSERT SQL generados:")
        print(result.sql_inserts)
        
        print("\n📝 Resumen:")
        print(f"- Total de INSERT statements: {len(result.sql_inserts.split(';')) - 1}")
        
        # Generar archivo de texto con el resultado
        generate_result_file(result, youtube_url)
        
        # Generar archivo SQL separado
        generate_sql_file(result, youtube_url)
        
        # Generar archivo SQL con INSERT individuales
        generate_individual_sql_file(result, youtube_url)
        
    except Exception as e:
        print(f"❌ Error durante el procesamiento: {str(e)}")
        import traceback
        traceback.print_exc()

def generate_result_file(result, youtube_url):
    """
    Genera un archivo de texto con el resultado del procesamiento
    """
    try:
        # Crear nombre de archivo con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = youtube_url.split("v=")[1] if "v=" in youtube_url else "unknown"
        filename = f"transcript_result_{video_id}_{timestamp}.txt"
        
        # Contenido del archivo
        content = f"""PROCESAMIENTO DE TRANSCRIPCIÓN DE YOUTUBE
{'='*60}
Fecha y hora: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
URL del video: {youtube_url}
Video ID: {video_id}

{'='*60}
RESUMEN DEL PROCESAMIENTO
{'='*60}
- Total de INSERT statements generados: {len(result.sql_inserts.split(';')) - 1}
- Estado: Completado exitosamente

{'='*60}
DATOS PROCESADOS
{'='*60}
{json.dumps(result.processed_data, indent=2, ensure_ascii=False)}

{'='*60}
INSERT SQL GENERADOS
{'='*60}
{result.sql_inserts}

{'='*60}
INSTRUCCIONES DE USO
{'='*60}
1. Copia y pega los INSERT SQL en tu base de datos PostgreSQL
2. Los UUIDs se generarán automáticamente usando gen_random_uuid()
3. Las fechas se establecen automáticamente con now()
4. Verifica que las tablas existan antes de ejecutar los INSERT

{'='*60}
ESTRUCTURA DE TABLAS REQUERIDA
{'='*60}
- lessons: Tabla principal de lecciones
- clips: Segmentos de video procesados  
- vocabulary: Vocabulario extraído para aprendizaje

{'='*60}
FIN DEL ARCHIVO
{'='*60}
"""
        
        # Escribir archivo
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n💾 Archivo de resultado generado: {filename}")
        print(f"📁 Ubicación: {os.path.abspath(filename)}")
        
        # Mostrar estadísticas del archivo
        file_size = os.path.getsize(filename)
        print(f"📊 Tamaño del archivo: {file_size} bytes ({file_size/1024:.2f} KB)")
        
    except Exception as e:
        print(f"❌ Error generando archivo de resultado: {str(e)}")

def generate_sql_file(result, youtube_url):
    """
    Genera un archivo SQL separado con solo los INSERT statements.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = youtube_url.split("v=")[1] if "v=" in youtube_url else "unknown"
        filename = f"transcript_sql_inserts_{video_id}_{timestamp}.sql"
        
        # Contenido del archivo SQL con formato profesional
        sql_content = f"""-- =====================================================
-- INSERT SQL GENERADOS AUTOMÁTICAMENTE
-- =====================================================
-- Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Video ID: {video_id}
-- URL: {youtube_url}
-- Total de INSERT statements: {len(result.sql_inserts.split(';')) - 1}
-- =====================================================

-- IMPORTANTE: Ejecutar este script en una base de datos PostgreSQL
-- con las tablas lessons, clips y vocabulary ya creadas.

-- =====================================================
-- INICIO DE TRANSACCIÓN
-- =====================================================

{result.sql_inserts}

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
-- Script generado automáticamente por el procesador de transcripciones
-- Verificar que todas las inserciones se hayan ejecutado correctamente
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sql_content)
        
        print(f"\n💾 Archivo de INSERT SQL generado: {filename}")
        print(f"📁 Ubicación: {os.path.abspath(filename)}")
        file_size = os.path.getsize(filename)
        print(f"📊 Tamaño del archivo: {file_size} bytes ({file_size/1024:.2f} KB)")
        
        # Mostrar estadísticas del archivo SQL
        sql_lines = result.sql_inserts.count('\n') + 1
        print(f"📝 Líneas de SQL: {sql_lines}")
        
    except Exception as e:
        print(f"❌ Error generando archivo de INSERT SQL: {str(e)}")

def generate_individual_sql_file(result, youtube_url):
    """
    Genera un archivo SQL con solo los INSERT statements individuales.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_id = youtube_url.split("v=")[1] if "v=" in youtube_url else "unknown"
        filename = f"transcript_sql_individual_inserts_{video_id}_{timestamp}.sql"

        # Contenido del archivo SQL con formato profesional
        sql_content = f"""-- =====================================================
-- INSERT SQL GENERADOS AUTOMÁTICAMENTE (Individuales)
-- =====================================================
-- Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Video ID: {video_id}
-- URL: {youtube_url}
-- Total de INSERT statements: {len(result.sql_inserts.split(';')) - 1}
-- =====================================================

-- IMPORTANTE: Ejecutar este script en una base de datos PostgreSQL
-- con las tablas lessons, clips y vocabulary ya creadas.

-- =====================================================
-- INICIO DE TRANSACCIÓN
-- =====================================================

{result.sql_inserts}

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================
-- Script generado automáticamente por el procesador de transcripciones
-- Verificar que todas las inserciones se hayan ejecutado correctamente
"""

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(sql_content)

        print(f"\n💾 Archivo de INSERT SQL individual generado: {filename}")
        print(f"📁 Ubicación: {os.path.abspath(filename)}")
        file_size = os.path.getsize(filename)
        print(f"📊 Tamaño del archivo: {file_size} bytes ({file_size/1024:.2f} KB)")

        # Mostrar estadísticas del archivo SQL
        sql_lines = result.sql_inserts.count('\n') + 1
        print(f"📝 Líneas de SQL: {sql_lines}")

    except Exception as e:
        print(f"❌ Error generando archivo de INSERT SQL individual: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando prueba del procesador de transcripciones...")
    asyncio.run(test_transcript_processor())
