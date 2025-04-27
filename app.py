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
progress = {"current": 0, "total": 0}
resultados_global = []

async def get_representative_id(session, email, empresa, session_cookies):
    """Obtiene el ID del representante de la empresa a partir del email"""
    url = f"{BASE_URL}/admin/companies/{empresa}/company_representatives"
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
        
        return link["href"].split("/")[-1]

async def get_preenchimento_values(session, rep_id, empresa, session_cookies):
    """Obtiene los valores de 'Preenchimento' desde la página de detalles"""
    url = f"{BASE_URL}/admin/companies/{empresa}/company_representatives/{rep_id}"
    
    async with session.get(url, cookies=session_cookies) as response:
        if response.status != 200:
            return None, None

        soup = BeautifulSoup(await response.text(), "html.parser")
        tables = soup.find_all("table", class_="table")
        
        preenchimento_values = []
        for table in tables:
            row = table.find("tbody").find("tr")
            td_preenchimento = row.find_all("td")[1].text.strip()
            preenchimento_values.append(td_preenchimento)
        
        return preenchimento_values if len(preenchimento_values) == 2 else (None, None)

async def fetch_data_for_email(session, email, empresa, session_cookies, total_emails, lock):
    """Procesa un email y retorna un diccionario con los resultados"""
    rep_id = await get_representative_id(session, email, empresa, session_cookies)
    if not rep_id:
        result = {"email": email, "genius_co": None, "workstyle": None}
    else:
        genius_co, workstyle = await get_preenchimento_values(session, rep_id, empresa, session_cookies)
        result = {"email": email, "genius_co": genius_co, "workstyle": workstyle}

    async with lock:
        progress["current"] += 1
        print(f"Progreso: {progress['current']}/{total_emails} emails procesados.")
    
    return result

async def fetch_data_for_emails(emails, empresa, session_cookies):
    """Procesa una lista de emails de forma asíncrona y retorna los resultados"""
    total_emails = len(emails)
    progress["current"] = 0
    progress["total"] = total_emails
    lock = asyncio.Lock()

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data_for_email(session, email, empresa, session_cookies, total_emails, lock) for email in emails]
        return await asyncio.gather(*tasks)

@app.route('/')
def index():
    """Renderiza el formulario HTML"""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_csv():
    """Procesa el archivo CSV y redirige a la página de progreso"""
    global resultados_global

    if 'file' not in request.files or request.files['file'].filename == '':
        return "No se proporcionó un archivo CSV", 400

    file = request.files['file']
    empresa = request.form.get('empresa')
    session_value = request.form.get('session')

    if not empresa or not session_value:
        return "Faltan valores para 'Empresa' o 'Session'", 400

    emails = []
    csv_file = file.stream.read().decode("utf-8").splitlines()
    reader = csv.reader(csv_file)
    next(reader)
    for row in reader:
        emails.append(row[0])

    session_cookies = {"_assessmentsApp_session": session_value}

    def run_async_task(emails, empresa, cookies):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(fetch_data_for_emails(emails, empresa, cookies))

    executor = ThreadPoolExecutor()
    future = executor.submit(run_async_task, emails, empresa, session_cookies)

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
    global resultados_global

    if progress["current"] < progress["total"]:
        return render_template('download.html', progress=progress)
    
    return render_template('completed.html')

@app.route('/completed')
def completed():

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["email", "genius_co", "workstyle"])
    writer.writeheader()
    writer.writerows(resultados_global)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='resultados.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)