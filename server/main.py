from fastapi import FastAPI, HTTPException, Request, status, Depends
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
from langchain_openai import ChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
import uvicorn
import os
import asyncio
import json
import re
from typing import List, Dict, Any
import requests

load_dotenv()

app = FastAPI(title="Quality Assurance Agent Server", version="1.0.0")

# Global crawler instance
crawler = None
crawler_lock = asyncio.Lock()

API_KEY = os.getenv("QA_API_KEY")
if not API_KEY:
    raise RuntimeError("QA_API_KEY not set in environment variables")

def verify_api_key(request: Request):
    api_key = request.headers.get("x-api-key")
    if api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key")

class CrawlRequest(BaseModel):
    url: str

class CrawlResponse(BaseModel):
    markdown_content: str
    url: str

class BrowserAgentRequest(BaseModel):
    prompt: str

class BrowserAgentResponse(BaseModel):
    result: str
    prompt: str
    model_actions: str | None = None
    screenshots: str | None = None

class YouTubeTranscriptRequest(BaseModel):
    url: str
    translate_code: str

class YouTubeTranscriptResponse(BaseModel):
    transcript: list
    video_id: str
    url: str
    language: str

class ProcessTranscriptRequest(BaseModel):
    url: str
    prompt: str

class ProcessTranscriptResponse(BaseModel):
    sql_inserts: str
    processed_data: dict

async def get_crawler():
    """Get or create the global crawler instance"""
    global crawler
    async with crawler_lock:
        if crawler is None:
            crawler = AsyncWebCrawler()
            await crawler.start()
        return crawler

def get_youtube_video_title(video_id: str) -> str:
    """
    Obtiene el título real del video de YouTube
    """
    try:
        # Intentar obtener el título usando la API pública de YouTube
        url = f"https://www.youtube.com/watch?v={video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            # Buscar el título en el HTML de la página
            html_content = response.text
            
            # Buscar el título en diferentes patrones comunes
            title_patterns = [
                r'<title>(.*?)</title>',
                r'"title":"([^"]+)"',
                r'<meta property="og:title" content="([^"]+)"',
                r'<meta name="title" content="([^"]+)"',
                r'"videoTitle":"([^"]+)"',
                r'"title":"([^"]+)"'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, html_content)
                if match:
                    title = match.group(1)
                    # Limpiar el título
                    title = title.replace(' - YouTube', '').replace(' | YouTube', '')
                    title = title.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
                    title = title.strip()
                    if title and len(title) > 5:  # Verificar que el título sea válido
                        # Limitar la longitud del título para la base de datos
                        if len(title) > 200:
                            title = title[:197] + "..."
                        return title
            
            # Si no se encuentra con los patrones, usar un título por defecto
            return f"Video {video_id}"
        else:
            print(f"Error HTTP {response.status_code} al obtener título del video")
            return f"Video {video_id}"
            
    except requests.exceptions.Timeout:
        print(f"Timeout al obtener título del video {video_id}")
        return f"Video {video_id}"
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión al obtener título del video: {str(e)}")
        return f"Video {video_id}"
    except Exception as e:
        print(f"Error inesperado obteniendo título del video: {str(e)}")
        return f"Video {video_id}"

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_website(request: CrawlRequest, _: None = Depends(verify_api_key)):
    """
    Crawl a website and return its markdown content
    """
    try:
        print(f"[debug-server] crawl_website({request.url})")
        crawler_instance = await get_crawler()
        result = await crawler_instance.arun(url=request.url)
        return CrawlResponse(
            markdown_content=result.markdown,
            url=request.url
        )
    except Exception as e:
        print(f"[debug-server] Error crawling website: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error crawling website: {str(e)}")

@app.post("/browser-agent", response_model=BrowserAgentResponse)
async def browser_agent(request: BrowserAgentRequest, _: None = Depends(verify_api_key)):
    """
    Run a browser agent with the given prompt
    """
    try:
        print(f"[debug-server] browser_agent({request.prompt})")
        llm = ChatOpenAI(model="gpt-4o")
        
        # Create browser configuration with headless mode
        browser_config = BrowserConfig(headless=True)
        browser = Browser(config=browser_config)
        
        agent = Agent(
            task=request.prompt,
            llm=llm,
            browser=browser
        )
        result = await agent.run()
        print(result.final_result())
        
        # Extract model_actions and screenshots if available
        model_actions = None
        screenshots = None
        
        try:
            # Try to get model_actions from the result
            if hasattr(result, 'model_actions') and callable(result.model_actions):
                model_actions = result.model_actions()
            elif hasattr(result, 'result') and hasattr(result.result, 'model_actions') and callable(result.result.model_actions):
                model_actions = result.result.model_actions()
        except Exception as e:
            print(f"Warning: Could not extract model_actions: {str(e)}")
        
        try:
            # Try to get screenshots from the result
            if hasattr(result, 'screenshots') and callable(result.screenshots):
                screenshots = result.screenshots()
            elif hasattr(result, 'result') and hasattr(result.result, 'screenshots') and callable(result.result.screenshots):
                screenshots = result.result.screenshots()
        except Exception as e:
            print(f"Warning: Could not extract screenshots: {str(e)}")
        
        # Close the browser after use
        await browser.close()
        
        return BrowserAgentResponse(
            result=result.final_result(),
            prompt=request.prompt,
            model_actions=model_actions,
            screenshots=screenshots
        )
    except Exception as e:
        print(f"[debug-server] Error running browser agent: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error running browser agent: {str(e)}")

@app.post("/youtube-transcript", response_model=YouTubeTranscriptResponse)
async def youtube_transcript(request: YouTubeTranscriptRequest, _: None = Depends(verify_api_key)):
    """
    Extract transcript from a YouTube video URL
    """
    try:
        print(f"[debug-server] youtube_transcript({request.url})")
        
        # Parse the URL
        parsed_url = urlparse(request.url)
        # Extract URL parameters
        query_params = parse_qs(parsed_url.query)
        # Get the 'v' parameter value
        video_id = query_params.get("v", [None])[0]
        
        if not video_id:
            raise HTTPException(status_code=400, detail="Invalid YouTube URL. Could not extract video ID.")
        
        # Fetch transcript
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        
        # Get raw data
        data = fetched_transcript.to_raw_data()

        if data[-1]['start'] + data[-1]['duration'] > 1000:
            raise HTTPException(status_code=400, detail="Video is too long. Please select a shorter video.")
        
        
        # Process the transcript data to add end times
        for i in range(len(data) - 1):
            data[i]['end'] = data[i + 1]['start']
        
        # Last element: end = start + duration + 1 second extra for better playback
        data[-1]['end'] = data[-1]['start'] + data[-1]['duration'] + 1
        
        return YouTubeTranscriptResponse(
            transcript=data,
            video_id=video_id,
            url=request.url,
            language=fetched_transcript.language_code,
            translate_code=request.translate_code
        )
    except Exception as e:
        print(f"[debug-server] Error extracting YouTube transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting YouTube transcript: {str(e)}")

async def process_transcript_and_generate_sql(url: str, prompt: str) -> ProcessTranscriptResponse:
    """
    Procesa una transcripción de YouTube y genera INSERT SQL para la base de datos
    """
    try:
        # 1. Obtener la transcripción
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        video_id = query_params.get("v", [None])[0]
        
        if not video_id:
            raise ValueError("Invalid YouTube URL. Could not extract video ID.")
        
        # Obtener transcripción
        ytt_api = YouTubeTranscriptApi()
        fetched_transcript = ytt_api.fetch(video_id)
        raw_data = fetched_transcript.to_raw_data()
        
        # 2. Procesar la transcripción según el prompt
        processed_data = await process_transcript_with_ai(raw_data, prompt, video_id, url)
        
        # 3. Generar INSERT SQL
        sql_inserts = generate_sql_inserts(processed_data, video_id, url)
        
        return ProcessTranscriptResponse(
            sql_inserts=sql_inserts,
            processed_data=processed_data
        )
        
    except Exception as e:
        print(f"Error processing transcript: {str(e)}")
        raise e

async def process_transcript_with_ai(transcript_data: List[Dict], prompt: str, video_id: str, url: str) -> Dict:
    """
    Procesa la transcripción usando IA para agrupar clips, traducir y extraer vocabulario
    """
    # Crear el prompt completo para la IA
    system_prompt = f"""
    Actúa como un procesador de transcripciones de video para una aplicación de aprendizaje de idiomas. 
    
    {prompt}
    
    Procesa la siguiente transcripción y devuelve solo el JSON transformado sin texto adicional.
    """
    
    # Preparar los datos para la IA
    input_data = {
        "transcript": transcript_data,
        "video_id": video_id,
        "url": url,
        "language": "en"
    }
    
    # Usar OpenAI para procesar
    llm = ChatOpenAI(model="gpt-4o")
    
    # Crear el mensaje completo
    full_prompt = f"{system_prompt}\n\nJSON a procesar:\n{json.dumps(input_data, indent=2)}"
    
    response = await llm.ainvoke(full_prompt)
    
    try:
        # Extraer el JSON de la respuesta
        response_text = response.content
        # Buscar el JSON en la respuesta
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            processed_data = json.loads(json_match.group())
            return processed_data
        else:
            raise ValueError("No se pudo extraer JSON válido de la respuesta de la IA")
    except json.JSONDecodeError as e:
        print(f"Error parsing AI response: {e}")
        print(f"AI Response: {response_text}")
        raise ValueError(f"Error parsing AI response: {e}")

def generate_sql_inserts(processed_data: Dict, video_id: str, url: str) -> str:
    """
    Genera todos los INSERT SQL necesarios para la base de datos
    """
    sql_statements = []
    
    # Calcular la duración total de la lección desde el último clip
    total_duration = "0"  # Por defecto en segundos
    if 'transcript' in processed_data and isinstance(processed_data['transcript'], list) and len(processed_data['transcript']) > 0:
        last_clip = processed_data['transcript'][-1]
        total_duration_seconds = last_clip.get('end', 0)
        # Mantener la duración en segundos para la base de datos
        total_duration = str(int(total_duration_seconds))
    
    # Agregar inicio de transacción
    sql_statements.append("BEGIN;")
    
    # 1. INSERT para la tabla lessons
    title = get_youtube_video_title(video_id)  # Obtener título real del video
    language = "en"
    target_language = "English"
    thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    
    lesson_insert = f"""
-- Insertar lección con duración calculada desde el último clip
-- Título: {title}
-- Duración total: {total_duration} segundos (calculada desde end del último clip)
INSERT INTO public.lessons (id, title, language, target_language, youtube_url, youtube_video_id, duration, thumbnail_url, status, created_at, updated_at)
VALUES (gen_random_uuid(), '{title}', '{language}', '{target_language}', '{url}', '{video_id}', '{total_duration}', '{thumbnail_url}', 'ready', now(), now());"""
    
    sql_statements.append(lesson_insert)
    
    # 2. INSERT para la tabla clips
    if 'transcript' in processed_data and isinstance(processed_data['transcript'], list):
        for i, clip in enumerate(processed_data['transcript']):
            start_time = clip.get('start', 0)
            end_time = clip.get('end', 0)
            original_text = clip.get('text', '').replace("'", "''")  # Escapar comillas simples
            translated_text = clip.get('text_translate', '').replace("'", "''")
            order_index = i + 1
            
            clip_insert = f"""
-- Insertar clip {i+1}
-- Nota: La duración incluye 1 segundo extra para mejor reproducción
INSERT INTO public.clips (id, lesson_id, start_time, end_time, original_text, translated_text, order_index, created_at)
SELECT 
    gen_random_uuid(),
    l.id,
    {start_time},
    {end_time},
    '{original_text}',
    '{translated_text}',
    {order_index},
    now()
FROM public.lessons l 
WHERE l.youtube_video_id = '{video_id}'
ORDER BY l.created_at DESC 
LIMIT 1;"""
            
            sql_statements.append(clip_insert)
            
            # 3. INSERT para la tabla vocabulary
            if 'vocabulary' in clip and isinstance(clip['vocabulary'], list):
                for j, vocab in enumerate(clip['vocabulary']):
                    original_word = vocab.get('original_word', '').replace("'", "''")
                    translation = vocab.get('translation', '').replace("'", "''")
                    notes = vocab.get('notes', '').replace("'", "''") if vocab.get('notes') else None
                    
                    vocab_insert = f"""
-- Insertar vocabulario {j+1} del clip {i+1}
INSERT INTO public.vocabulary (id, clip_id, original_word, translation, notes, created_at)
SELECT 
    gen_random_uuid(),
    c.id,
    '{original_word}',
    '{translation}',
    {f"'{notes}'" if notes else 'NULL'},
    now()
FROM public.clips c
JOIN public.lessons l ON c.lesson_id = l.id
WHERE l.youtube_video_id = '{video_id}' 
AND c.order_index = {order_index}
LIMIT 1;"""
                    
                    sql_statements.append(vocab_insert)
    
    # Agregar commit
    sql_statements.append("COMMIT;")
    
    return "\n".join(sql_statements)

@app.post("/process-transcript", response_model=ProcessTranscriptResponse)
async def process_transcript_endpoint(request: ProcessTranscriptRequest, _: None = Depends(verify_api_key)):
    """
    Procesa una transcripción de YouTube y genera INSERT SQL para la base de datos
    """
    try:
        print(f"[debug-server] process_transcript({request.url}, {request.prompt})")
        
        result = await process_transcript_and_generate_sql(request.url, request.prompt)
        
        return result
        
    except Exception as e:
        print(f"[debug-server] Error processing transcript: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing transcript: {str(e)}")

@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Quality Assurance Agent Server",
        "version": "1.0.0",
        "endpoints": {
            "crawl": "/crawl - POST - Crawl a website",
            "browser_agent": "/browser-agent - POST - Run browser agent",
            "youtube_transcript": "/youtube-transcript - POST - Extract YouTube video transcript",
            "process_transcript": "/process-transcript - POST - Process transcript and generate SQL inserts"
        }
    }

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when the server shuts down"""
    global crawler
    if crawler:
        await crawler.close()

if __name__ == "__main__":
    # Get host and port from environment variables with defaults
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    port = int(os.getenv("SERVER_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port)