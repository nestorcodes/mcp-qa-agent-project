# 1. IMPORTAR LAS HERRAMIENTAS NECESARIAS
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, NoSuchFrameException
import time
import os

# --- DICCIONARIO PARA TRADUCIR PAÍSES ---
traductor_paises = {
    'Honduras': 'HN',
    'El Salvador': 'SV',
    'México': 'MX',
    'Costa Rica': 'CR',
    'Colombia': 'CO',
    'Nicaragua': 'NI'
}

# --- CONFIGURACIÓN ---
# Excel en la MISMA carpeta que este script
RUTA_BASE = os.path.dirname(__file__)
ruta_excel = os.path.join(RUTA_BASE, "Evento Netsuite 2.xlsx")
url_formulario = "https://go.netsuite.com/LP=26321?leadsource=Webinar_LAD_Horiz_LiderandoFinanzas_ComparaSoftware_0825"

# --- FUNCIÓN PARA MANEJAR COOKIES DE FORMA NO BLOQUEANTE ---
def manejar_cookies(driver, timeout_seconds: int = 2):
    """
    Intenta encontrar y aceptar el banner de cookies con múltiples estrategias.
    Si no se encuentra rápidamente, devuelve False sin bloquear el flujo.
    """
    print("   -> Buscando banner de cookies...")
    short_wait = WebDriverWait(driver, timeout_seconds)
    
    # Lista de estrategias para encontrar y aceptar cookies
    estrategias = [
        # Estrategia 1: TrustArc iframe por nombre específico
        {
            'tipo': 'trustarc_notice',
            'iframe': 'trustarc_notice',
            'selector': "//a[@class='call' and contains(text(), 'Aceptar todas')]"
        },
        # Estrategia 2: TrustArc iframe de configuración
        {
            'tipo': 'trustarc_cm',
            'iframe': 'trustarc_cm', 
            'selector': "//a[@class='call' and contains(text(), 'Aceptar todas')]"
        },
        # Estrategia 3: TrustArc iframe por selector genérico
        {
            'tipo': 'trustarc_call_button',
            'iframe': 'trustarc_notice',
            'selector': "//a[@class='call']"
        },
        # Estrategia 4: TrustArc cualquier botón de aceptar
        {
            'tipo': 'trustarc_aceptar',
            'iframe': 'trustarc_notice',
            'selector': "//a[contains(text(), 'Aceptar')]"
        },
        # Estrategia 5: Buscar directamente sin iframe
        {
            'tipo': 'directo_trustarc',
            'iframe': None,
            'selector': "//a[contains(@class, 'truste') and contains(text(), 'Aceptar')]"
        }
    ]
    
    for i, estrategia in enumerate(estrategias, 1):
        try:
            print(f"   -> Probando estrategia {i}: {estrategia['tipo']}")
            
            # Estrategias específicas para TrustArc
            if estrategia['tipo'] == 'trustarc_iframe_id':
                try:
                    # Buscar iframe con ID que empiece con "pop-frame"
                    iframes = driver.find_elements(By.XPATH, "//iframe[starts-with(@id, 'pop-frame')]")
                    if iframes:
                        driver.switch_to.frame(iframes[0])
                        iframe_id = iframes[0].get_attribute("id")
                        print(f"   -> Entrando al iframe TrustArc: {iframe_id}")
                    else:
                        print("   -> No se encontró iframe TrustArc por ID")
                        continue
                except:
                    continue
                    
            elif estrategia['tipo'] == 'trustarc_iframe_attrs':
                try:
                    # Buscar iframe de TrustArc por título
                    iframe_trustarc = short_wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//iframe[contains(@title, 'TrustArc') or contains(@title, 'Cookie')]")
                    ))
                    driver.switch_to.frame(iframe_trustarc)
                    print("   -> Entrando al iframe TrustArc por título")
                except TimeoutException:
                    print("   -> No se encontró iframe TrustArc por título")
                    continue
                    
            elif estrategia['iframe']:
                # Estrategia con iframe específico por nombre
                try:
                    short_wait.until(EC.frame_to_be_available_and_switch_to_it((By.NAME, estrategia['iframe'])))
                    print(f"   -> Entrando al iframe: {estrategia['iframe']}")
                except TimeoutException:
                    print(f"   -> No se encontró iframe: {estrategia['iframe']}")
                    continue
            
            # Buscar y hacer clic en el botón/enlace de cookies
            try:
                elemento_cookie = short_wait.until(EC.element_to_be_clickable((By.XPATH, estrategia['selector'])))
                elemento_cookie.click()
                print(f"   ✅ Cookies aceptadas con estrategia {i}")
                driver.switch_to.default_content()
                time.sleep(2)  # Esperar a que el banner desaparezca
                return True
            except TimeoutException:
                print(f"   -> No se encontró elemento con selector: {estrategia['selector']}")
                driver.switch_to.default_content()
                # Si no se encontró rápidamente, devolvemos False para no bloquear
                return False
                
        except Exception as e:
            print(f"   -> Error en estrategia {i}: {str(e)}")
            driver.switch_to.default_content()
            # Cualquier error al manejar cookies no debe bloquear el flujo
            return False
    
    print("   ⚠️ No se pudo encontrar/aceptar banner de cookies con ninguna estrategia")
    return False

# --- FUNCIÓN PARA INSPECCIONAR LA PÁGINA ---
def inspeccionar_pagina(driver):
    """
    Inspecciona la página para encontrar elementos relacionados con cookies
    """
    print("\n--- INSPECCIÓN DE LA PÁGINA ---")
    
    # Buscar iframes
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"Iframes encontrados: {len(iframes)}")
    for i, iframe in enumerate(iframes):
        try:
            name = iframe.get_attribute("name") or "sin nombre"
            src = iframe.get_attribute("src") or "sin src"
            print(f"  Iframe {i+1}: name='{name}', src='{src[:50]}...'")
        except:
            print(f"  Iframe {i+1}: Error al obtener atributos")
    
    # Buscar elementos que contengan "cookie" en el texto o atributos
    elementos_cookie = driver.find_elements(By.XPATH, "//*[contains(text(), 'cookie') or contains(text(), 'Cookie') or contains(@class, 'cookie') or contains(@id, 'cookie')]")
    print(f"\nElementos relacionados con cookies: {len(elementos_cookie)}")
    for elemento in elementos_cookie[:5]:  # Mostrar solo los primeros 5
        try:
            tag = elemento.tag_name
            text = elemento.text[:50] if elemento.text else "sin texto"
            clase = elemento.get_attribute("class") or "sin clase"
            print(f"  {tag}: text='{text}', class='{clase}'")
        except:
            print("  Elemento: Error al obtener información")

# --- EL CÓDIGO DE AUTOMATIZACIÓN PRINCIPAL ---

# LEER LOS DATOS DEL ARCHIVO EXCEL
try:
    df = pd.read_excel(ruta_excel)
    print(f"✅ Se han cargado {len(df)} registros del archivo Excel.")
except FileNotFoundError:
    print(f"❌ ERROR: No se encontró el archivo Excel en la ruta: {ruta_excel}")
    exit()

# CONFIGURAR OPCIONES DEL NAVEGADOR
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

# INICIAR EL NAVEGADOR (Selenium Manager gestiona el WebDriver automáticamente)
driver = webdriver.Chrome(options=chrome_options)
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
print("🤖 Navegador iniciado.")

# --- CREAR ARCHIVOS DE LOG ---
log_exitosos_path = os.path.join(RUTA_BASE, "log_exitosos.txt")
log_errores_path = os.path.join(RUTA_BASE, "log_errores.txt")

# Crear archivos de log si no existen
with open(log_exitosos_path, "w", encoding="utf-8") as f:
    f.write(f"=== LOG DE REGISTROS EXITOSOS - INICIADO: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

with open(log_errores_path, "w", encoding="utf-8") as f:
    f.write(f"=== LOG DE REGISTROS CON ERRORES - INICIADO: {time.strftime('%Y-%m-%d %H:%M:%S')} ===\n")

print(f"📝 Archivos de log creados:")
print(f"   ✅ Éxitos: {log_exitosos_path}")
print(f"   ❌ Errores: {log_errores_path}")
print(f"🚀 Iniciando procesamiento de {len(df)} registros...")

# RECORRER TODAS LAS FILAS DEL EXCEL
for index, row in df.iterrows():
    email_actual = row.get('email', 'Email no encontrado')
    print(f"\nProcesando registro {index + 1} de {len(df)}: {email_actual}")

    try:
        driver.get(url_formulario)
        wait = WebDriverWait(driver, 15)  # Aumentado el tiempo de espera
        
        # Esperar a que la página cargue completamente
        time.sleep(3)
        
        # OPCIÓN: Inspeccionar la página para debug (comentar en producción)
        if index == 0:  # Solo en el primer registro para debug
            inspeccionar_pagina(driver)
            
            # DEBUG ADICIONAL: Capturar screenshot y HTML
            driver.save_screenshot(os.path.join(RUTA_BASE, f"debug_screenshot_{index}.png"))
            with open(os.path.join(RUTA_BASE, f"debug_page_source_{index}.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"   -> Screenshot y HTML guardados para debug")
        
        # --- MANEJAR COOKIES (no bloqueante) ---
        cookies_aceptadas = manejar_cookies(driver)
        
        # Si no se pudieron aceptar cookies, intentar continuar de todas formas
        if not cookies_aceptadas:
            print("   -> Continuando sin aceptar cookies...")
        
        # Esperar un poco después de manejar cookies
        time.sleep(3)

        # --- RELLENAR CAMPOS DE TEXTO (fuera del iframe) ---
        print("   -> Rellenando campos principales...")
        try:
            # Esperar más tiempo para que la página cargue completamente después de cookies
            time.sleep(2)
            
            # Verificar que los campos existen antes de rellenarlos
            print("   -> Buscando campo firstName...")
            first_name_field = wait.until(EC.element_to_be_clickable((By.ID, "firstName")))
            first_name_field.clear()
            first_name_field.send_keys(str(row["first_name"]))
            print(f"   -> Nombre rellenado: {row['first_name']}")
            
            print("   -> Buscando campo lastName...")
            last_name_field = wait.until(EC.element_to_be_clickable((By.ID, "lastName")))
            last_name_field.clear()
            last_name_field.send_keys(str(row["last_name"]))
            print(f"   -> Apellido rellenado: {row['last_name']}")
            
            print("   -> Buscando campo emailAddress...")
            email_field = wait.until(EC.element_to_be_clickable((By.ID, "emailAddress")))
            email_field.clear()
            email_field.send_keys(str(row["email"]))
            print(f"   -> Email rellenado: {row['email']}")
            
            print("   -> Buscando campo company...")
            company_field = wait.until(EC.element_to_be_clickable((By.ID, "company")))
            company_field.clear()
            company_field.send_keys(str(row["company_name"]))
            print(f"   -> Empresa rellenada: {row['company_name']}")
            
            print("   -> Buscando campo phone...")
            phone_field = wait.until(EC.element_to_be_clickable((By.ID, "phone")))
            phone_field.clear()
            phone_field.send_keys(str(row["phone_number"]))
            print(f"   -> Teléfono rellenado: {row['phone_number']}")
                
        except Exception as e:
            print(f"   ❌ Error rellenando campos principales: {e}")
                        # Intentar alternativas si los IDs no funcionan
            print("   -> Intentando selectores alternativos...")
            try:
                # Buscar por name en lugar de id
                campos_alternativos = [
                    ("first_name", "firstName"),
                    ("last_name", "lastName"), 
                    ("email", "emailAddress"),
                    ("company_name", "company"),
                    ("phone_number", "phone")
                ]
                
                for campo_excel, campo_name in campos_alternativos:
                    try:
                        campo = driver.find_element(By.NAME, campo_name)
                        campo.clear()
                        campo.send_keys(str(row[campo_excel]))
                        print(f"   -> {campo_name} rellenado por NAME")
                    except:
                        print(f"   -> No se encontró campo {campo_name} por NAME")
                        
            except Exception as e2:
                print(f"   ❌ Error con selectores alternativos: {e2}")
                # Capturar screenshot para debug en caso de error
                driver.save_screenshot(os.path.join(RUTA_BASE, f"error_screenshot_{index}.png"))
                raise e

        # --- RELLENAR CAMPOS ADICIONALES (sin iframe) ---
        try:
            print("   -> Rellenando campos adicionales...")
            
            # --- SELECCIONAR PAÍS ---
            nombre_pais_excel = row["País"]
            codigo_pais_form = traductor_paises.get(nombre_pais_excel)
            if codigo_pais_form:
                Select(driver.find_element(By.ID, "country")).select_by_value(codigo_pais_form)
                print(f"   -> País seleccionado: {nombre_pais_excel} -> {codigo_pais_form}")
            else:
                print(f"   ⚠️ AVISO: El país '{nombre_pais_excel}' no se encontró en el traductor.")

            # SELECCIONAR VALORES FIJOS
            Select(driver.find_element(By.ID, "acctBusinessType1")).select_by_value("55")
            Select(driver.find_element(By.ID, "acctAnnualRevenue1")).select_by_value("26")
            
            print("   -> Campos adicionales rellenados.")
            
        except Exception as e:
            print(f"   ⚠️ Error rellenando campos adicionales: {e}")
        
        # --- ENVIAR EL FORMULARIO ---
        print("   -> Enviando formulario...")
        submit_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Regístrate ahora']")
        submit_button.click()
        print("   ✅ Formulario enviado!")

        print("   ✅ Formulario rellenado y enviado exitosamente!")
        
        # --- GUARDAR LOG DE ÉXITO ---
        log_exitoso = f"✅ REGISTRO {index + 1} COMPLETADO: {email_actual} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        with open(os.path.join(RUTA_BASE, "log_exitosos.txt"), "a", encoding="utf-8") as f:
            f.write(log_exitoso)
        print(f"   📝 Log guardado: {log_exitoso.strip()}")
        
        # --- ESPERAR 5 SEGUNDOS ANTES DEL SIGUIENTE REGISTRO ---
        if index < len(df) - 1:  # Si no es el último registro
            print("   ⏳ Esperando 5 segundos antes del siguiente registro...")
            time.sleep(5)
        else:
            print("   🎉 ¡Último registro procesado!")

    except Exception as e:
        print(f"   ❌ ERROR al procesar el registro {index + 1}: {e}")
        
        # --- GUARDAR LOG DE ERROR ---
        log_error = f"❌ REGISTRO {index + 1} FALLÓ: {email_actual} - ERROR: {str(e)} - {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        with open(os.path.join(RUTA_BASE, "log_errores.txt"), "a", encoding="utf-8") as f:
            f.write(log_error)
        print(f"   📝 Error logueado: {log_error.strip()}")
        
        driver.switch_to.default_content()  # Asegurar que estamos en el contexto principal
        
        # --- ESPERAR 5 SEGUNDOS ANTES DEL SIGUIENTE REGISTRO ---
        if index < len(df) - 1:  # Si no es el último registro
            print("   ⏳ Esperando 5 segundos antes del siguiente registro...")
            time.sleep(5)
        continue

# CERRAR EL NAVEGADOR AL FINALIZAR
driver.quit()
print("\n🎉 ¡Proceso completado!")