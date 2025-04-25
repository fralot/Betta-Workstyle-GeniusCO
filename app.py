from flask import Flask, request, render_template, send_file, redirect, url_for
import aiohttp
import asyncio
import csv
from bs4 import BeautifulSoup
import io
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configuración base
BASE_URL = "https://conheco.bettha.com"
progress = {"current": 0, "total": 0}  # Variable global para el progreso
resultados_global = []  # Variable global para almacenar los resultados

async def get_representative_id(session, email, processo, session_cookies):
    """Obtiene el ID del representante de la empresa a partir del email"""
    url = f"{BASE_URL}/admin/companies/{processo}/company_representatives"
    params = {
        "filters[name]": "",
        "filters[email]": email,
        "commit": "Filtrar"
    }
    
    async with session.get(url, params=params, cookies=session_cookies) as response:
        if response.status != 200:
            return None
        
        soup = BeautifulSoup(await response.text(), "html.parser")
        tbody = soup.find("tbody")
        if not tbody:
            return None
        
        link = tbody.find("a", href=True)
        if not link:
            return None
        
        # Extrae el ID de la URL del enlace
        return link["href"].split("/")[-1]

async def get_preenchimento_values(session, rep_id, processo, session_cookies):
    """Obtiene los valores de 'Preenchimento' desde la página de detalles"""
    url = f"{BASE_URL}/admin/companies/{processo}/company_representatives/{rep_id}"
    
    async with session.get(url, cookies=session_cookies) as response:
        if response.status != 200:
            return None, None

        soup = BeautifulSoup(await response.text(), "html.parser")
        tables = soup.find_all("table", class_="table")
        
        preenchimento_values = []
        for table in tables:
            row = table.find("tbody").find("tr")
            td_preenchimento = row.find_all("td")[1].text.strip()  # Segunda columna
            preenchimento_values.append(td_preenchimento)
        
        return preenchimento_values if len(preenchimento_values) == 2 else (None, None)

async def fetch_data_for_email(session, email, processo, session_cookies, total_emails, lock):
    """Procesa un email y retorna un diccionario con los resultados"""
    rep_id = await get_representative_id(session, email, processo, session_cookies)
    if not rep_id:
        result = {"email": email, "genius_co": None, "workstyle": None}
    else:
        genius_co, workstyle = await get_preenchimento_values(session, rep_id, processo, session_cookies)
        result = {"email": email, "genius_co": genius_co, "workstyle": workstyle}
        # print({"email": email, "genius_co": genius_co, "workstyle": workstyle})
    # Actualiza el contador de forma segura
    async with lock:
        progress["current"] += 1
        print(f"Progreso: {progress['current']}/{total_emails} emails procesados.")
    
    return result

async def fetch_data_for_emails(emails, processo, session_cookies):
    """Procesa una lista de emails de forma asíncrona y retorna los resultados"""
    total_emails = len(emails)
    progress["current"] = 0
    progress["total"] = total_emails
    lock = asyncio.Lock()  # Lock para proteger el acceso al contador

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data_for_email(session, email, processo, session_cookies, total_emails, lock) for email in emails]
        return await asyncio.gather(*tasks)

@app.route('/')
def index():
    """Renderiza el formulario HTML"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_csv():
    """Procesa el archivo CSV y redirige a la página de progreso"""
    global resultados_global  # Declarar la variable global para almacenar los resultados

    if 'file' not in request.files or request.files['file'].filename == '':
        return "No se proporcionó un archivo CSV", 400

    file = request.files['file']
    processo = request.form.get('processo')
    session_value = request.form.get('session')

    if not processo or not session_value:
        return "Faltan valores para 'Processo' o 'Session'", 400

    # Leer emails del archivo CSV
    emails = []
    csv_file = file.stream.read().decode("utf-8").splitlines()
    reader = csv.reader(csv_file)
    next(reader)  # Saltar el encabezado
    for row in reader:
        emails.append(row[0])  # Asume que los emails están en la primera columna

    # Configurar cookies
    session_cookies = {"_assessmentsApp_session": session_value}

    def run_async_task(emails, processo, cookies):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(fetch_data_for_emails(emails, processo, cookies))

    executor = ThreadPoolExecutor()
    future = executor.submit(run_async_task, emails, processo, session_cookies)

    def on_complete(f):
        global resultados_global
        try:
            resultados_global = f.result()
        except Exception as e:
            print(f"Error: {e}")

    future.add_done_callback(on_complete)

    return redirect(url_for('download'))

@app.route('/download')
def download():
    """Muestra la página de progreso o genera el archivo CSV si el procesamiento ha terminado"""
    global resultados_global  # Declarar la variable global para acceder a los resultados

    # Verificar si el procesamiento ha terminado
    if progress["current"] < progress["total"]:
        return render_template('download.html', progress=progress)
    
    # Generar el archivo CSV en memoria
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["email", "genius_co", "workstyle"])
    writer.writeheader()
    writer.writerows(resultados_global)  # Usar los resultados almacenados en la variable global
    output.seek(0)

    # Enviar el archivo al cliente
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='resultados.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)