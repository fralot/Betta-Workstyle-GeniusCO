# Verificación de Datos de Workstyle y Genius GO
Este proyecto es una aplicación web desarrollada en Flask que permite verificar los datos de los usuarios (emails) que realizaron las pruebas de **Workstyle** y **Genius GO** en la plataforma Betta. La aplicación procesa un archivo CSV con una lista de emails, junto con el número de la compañía (proceso) y la sesión de login, para obtener los resultados y generar un archivo CSV con la información procesada.

Link:
[Deploy App](https://betta-workstyle-geniusco-h3btaedgasdtbwgj.canadacentral-01.azurewebsites.net/)

## Funcionalidades
1. Carga de datos:

    - Permite cargar un archivo CSV con una lista de emails.
    - Requiere ingresar el número de la compañía (proceso) y la sesión de login (_assessmentsApp_session).

2. Procesamiento asíncrono:

    - Los datos se procesan de forma asíncrona para obtener la información de cada email desde la plataforma Betta.

3. Progreso en tiempo real:

    - Muestra el progreso del procesamiento en tiempo real en una página de carga.

4. Generación de resultados:

    - Una vez completado el procesamiento, genera un archivo CSV con los resultados, que incluye:
        - Email.
        - Genius GO.
        - Workstyle.

## Requisitos
- Dependencias
- Python 3.8 o superior.
- Flask.
- aiohttp.
- BeautifulSoup4.

Instalación de dependencias

Ejecuta el siguiente comando para instalar las dependencias necesarias:

``` py
pip install flask aiohttp beautifulsoup4
```

Estructura del proyecto

```
Betta/
├── Workstyle e Genius CO Azure deploy/
│   ├── app.py                # Código principal de la aplicación Flask
│   ├── templates/
│   │   ├── index.html        # Formulario para cargar el archivo CSV
│   │   ├── download.html     # Página de progreso
│   └── static/               # Archivos estáticos (opcional)
```

Uso

1. **Ejecutar la aplicación:** Ejecuta el archivo app.py para iniciar el servidor Flask:

```
python app.py
```

2. **Acceder a la aplicación:** Abre tu navegador y ve a http://127.0.0.1:5000.

3. **Cargar datos:**
    - En la página principal, selecciona un archivo CSV con la lista de emails.
    - Ingresa el número de la compañía (proceso).
    - Ingresa el valor de la sesión (_assessmentsApp_session).
    - Haz clic en "Enviar".

4. **Ver progreso:**

    - Serás redirigido a una página que muestra el progreso del procesamiento en tiempo real.

5. **Descargar resultados:**

    - Una vez completado el procesamiento, se generará un archivo ``resultados.csv`` que podrás descargar.

### Formato del archivo CSV
El archivo CSV debe tener la siguiente estructura:

```
email
usuario1@example.com
usuario2@example.com
usuario3@example.com
```

- La primera fila debe contener el encabezado email.
- Cada fila subsiguiente debe contener un email válido.

### **Notas importantes**
- **Sesión de login:**

    - El valor de ``_assessmentsApp_session`` debe ser válido y corresponder a una sesión activa en la plataforma Betta.
    - Si la sesión expira, el procesamiento fallará.
- **Número de la compañía (proceso):**

    - Este valor debe ser el identificador único de la compañía en la plataforma Betta.
- **Progreso en tiempo real:**

    - La página de progreso se actualiza automáticamente cada 2 segundos.

### Ejemplo de salida
El archivo ``resultados.csv`` generado tendrá el siguiente formato:

```
email,genius_co,workstyle
usuario1@example.com,2025-03-24 13:03,
usuario2@example.com,2025-03-19 16:18,2025-03-19 
usuario3@example.com,2025-03-08 17:49,2025-03-08 17:58

```

- Si no se encuentra información para un email, los valores de ``genius_co`` y ``workstyle`` serán ``None``.

### Contribuciones
Si deseas contribuir a este proyecto, puedes hacerlo mediante un pull request o reportando problemas en el repositorio.

### Licencia
Este proyecto está bajo la licencia MIT. Puedes usarlo, modificarlo y distribuirlo libremente.

