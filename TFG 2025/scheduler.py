import os
import json
import logging
import subprocess
import time
import threading
from datetime import datetime
import sys
import uuid 



sys.path.append('/home/marcos/2324_ASIR_MARCOS_ZARAGOZA_RIOS_JOB_SCHEDULER')

# Flask y ayudas que he ido necesitando
from flask import Flask, render_template, request, redirect, url_for, flash

# Librería schedule (para la programación)
import schedule

# Importamos las funciones y diccionario desde tasks.py, excluyendo load_config
from tasks import (
    task_functions,
    send_email,
    backup_and_transfer,
    get_logged_in_users_and_send_email,
    clean_trash
)

from tasks import task_functions, task_descriptions  # Importar los diccionarios de tareas


# Importar load_config y save_config desde config_utils.py
from config_utils import load_config, save_config




# Configuración de flask y logging
app = Flask(__name__)
app.secret_key = 'supersecretkey' 

CONFIG_FILE = 'config.json'
LOG_FILE = 'scheduler.log'

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


# Rutas de la aplicación Flask
@app.route('/')
def home():
    config = load_config()
    jobs_list = config.get('jobs', [])
    last_exec = config.get('last_execution', 'N/A')

    stats = {
        'num_jobs': len(jobs_list),
        'last_execution': last_exec
    }

    # Contar tipos de intervalos para el gráfico
    interval_counts = {}
    for job in jobs_list:
        interval = job.get('interval', 'unknown')
        interval_counts[interval] = interval_counts.get(interval, 0) + 1

    chart_data = {
        'labels': list(interval_counts.keys()),
        'values': list(interval_counts.values())
    }

    return render_template('home.html', stats=stats, chart_data=chart_data)

@app.route('/jobs')
def jobs():
    """Lista las tareas programadas."""
    config = load_config()
    all_jobs = config.get('jobs', [])
    return render_template('jobs.html', jobs=all_jobs)


@app.route('/add_job', methods=['GET', 'POST'])
def add_job():
    """Añade una nueva tarea programada."""
    if request.method == 'POST':
        # Obtener los datos del formulario
        task = request.form.get('task')
        interval = request.form.get('interval')
        time_ = request.form.get('time', None)
        minutes = request.form.get('minutes', None)
        minute = request.form.get('minute', None)
        script = request.form.get('script', None)

        # Validación básica
        if not task or not interval:
            flash('Tarea e intervalo son obligatorios.', 'danger')
            return redirect(url_for('add_job'))

        # Verificar que la tarea seleccionada existe
        if task not in task_functions and task not in task_descriptions:
            flash('La tarea seleccionada no es válida.', 'danger')
            return redirect(url_for('add_job'))

        config = load_config()
        if 'jobs' not in config:
            config['jobs'] = []

        # Crear un nuevo trabajo con un ID único
        new_job = {
            'id': str(uuid.uuid4()),  # genera un UUID único
            'task': task,
            'interval': interval
        }

        # Agregar campos adicionales si están presentes
        if time_:
            new_job['time'] = time_
        if minutes:
            try:
                new_job['minutes'] = int(minutes)
            except ValueError:
                flash('Los minutos deben ser un número entero positivo.', 'danger')
                return redirect(url_for('add_job'))
        if minute:
            try:
                new_job['minute'] = int(minute)
                if not (0 <= new_job['minute'] <= 59):
                    raise ValueError
            except ValueError:
                flash('El minuto debe ser un número entero entre 0 y 59.', 'danger')
                return redirect(url_for('add_job'))
        if script:
            new_job['script'] = script

        # Añadir el nuevo trabajo a la configuración
        config['jobs'].append(new_job)
        save_config(config)

        flash('Tarea añadida correctamente.', 'success')

        # Reprogramar las tareas en memoria (schedule)
        schedule_jobs()

        return redirect(url_for('jobs'))

    # Para solicitudes GET, pasar las tareas y descripciones a la plantilla
    tasks = [{'name': name, 'description': desc} for name, desc in task_descriptions.items()]
    return render_template('add_job.html', tasks=tasks)


@app.route('/logs')
def logs():
    """Muestra los logs."""
    try:
        with open(LOG_FILE, 'r') as log_file:
            log_content = log_file.readlines()
    except FileNotFoundError:
        log_content = ["No hay logs disponibles."]
    return render_template('logs.html', logs=log_content)

@app.route('/delete_log', methods=['POST'])
def delete_log():
    """Elimina el archivo de logs."""
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
        flash('Log eliminado correctamente.', 'success')
    else:
        flash('No se encontró ningún log para eliminar.', 'danger')
    return redirect(url_for('logs'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Permite modificar la configuración del sistema."""
    config = load_config()
    if request.method == 'POST':
        try:
            config['email']['smtp_server'] = request.form.get('smtp_server')
            config['email']['smtp_port']   = int(request.form.get('smtp_port'))
            config['email']['username']    = request.form.get('username')
            config['email']['password']    = request.form.get('password')
            config['memory_alert_threshold'] = int(request.form.get('memory_alert_threshold'))
            save_config(config)
            flash('Configuración actualizada correctamente.', 'success')
        except Exception as e:
            logging.error(f"Error al actualizar la configuración: {e}")
            flash('Error al actualizar la configuración.', 'danger')
    return render_template('settings.html', config=config)

@app.route('/delete_job', methods=['POST'])
def delete_job():
    """Elimina una tarea programada basada en su ID único."""
    try:
        job_id = request.form.get('job_id')
        if not job_id:
            flash("No se proporcionó el ID de la tarea.", 'danger')
            return redirect(url_for('jobs'))
        
        config = load_config()
        jobs_list = config.get('jobs', [])

        # Buscar la tarea por uuid usando .get para evitar error de key
        job_to_remove = next((job for job in jobs_list if job.get('id') == job_id), None)

        if job_to_remove:
            jobs_list.remove(job_to_remove)
            save_config(config)
            flash(f"Tarea '{job_to_remove.get('task', 'Desconocida')}' eliminada correctamente.", 'success')
            schedule_jobs()
        else:
            flash("ID de tarea inválido.", 'danger')
    except Exception as e:
        logging.error(f"Error al eliminar la tarea: {e}")
        flash("Ocurrió un error al eliminar la tarea.", 'danger')

    return redirect(url_for('jobs'))


# Lógica de scheduling con schedule

def schedule_jobs():
    """Lee config.json y programa las tareas en `schedule`."""
    schedule.clear()  # Limpia la programación previa

    config = load_config()
    jobs_list = config.get('jobs', [])

    for job in jobs_list:
        task_name  = job.get('task')
        interval   = job.get('interval')
        minutes    = job.get('minutes', None)
        minute     = job.get('minute', None)
        time_of_day= job.get('time', None)
        script     = job.get('script', None)

        # Determinar la función o el script
        func = task_functions.get(task_name, None)

        if not func and script:
            def script_runner(path=script):
                logging.info(f"Ejecutando script: {path}")
                print(f"Ejecutando script: {path}")
                try:
                    subprocess.run([path], check=True)
                except Exception as e:
                    logging.error(f"Error al ejecutar script {path}: {e}")
            func = script_runner

        if not func:
            logging.error(f"No hay función ni script para la tarea: {task_name}")
            continue

        # Programar la tarea según su interval
        if interval == 'daily' and time_of_day:
            schedule.every().day.at(time_of_day).do(func)
            logging.info(f"Tarea '{task_name}' programada diariamente a {time_of_day}")

        elif interval == 'hourly' and minute is not None:
            try:
                minute_int = int(minute)
                if not (0 <= minute_int <= 59):
                    raise ValueError("El minuto debe estar entre 0 y 59.")
                # Formatear con dos dígitos
                time_formatted = f":{minute_int:02d}"
                schedule.every().hour.at(time_formatted).do(func)
                logging.info(f"Tarea '{task_name}' programada cada hora en el minuto {minute_int}")
            except ValueError as ve:
                logging.warning(f"Minuto inválido para la tarea '{task_name}': {ve}")
                logging.warning(f"Intervalo no válido para '{task_name}'")

        elif interval == 'minute' and minutes is not None:
            try:
                minutes_int = int(minutes)
                if minutes_int <= 0:
                    raise ValueError("Los minutos deben ser mayores que 0.")
                schedule.every(minutes_int).minutes.do(func)
                logging.info(f"Tarea '{task_name}' programada cada {minutes_int} minutos")
            except ValueError as ve:
                logging.warning(f"Cantidad de minutos inválida para la tarea '{task_name}': {ve}")
                logging.warning(f"Intervalo no válido para '{task_name}'")

        else:
            logging.warning(f"Intervalo no válido para '{task_name}'")

    logging.info("Todas las tareas han sido programadas.")


def schedule_loop():
    """Bucle infinito que llama a `schedule.run_pending()` cada segundo."""
    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    """Inicia el hilo que corre `schedule_loop()` en segundo plano."""
    t = threading.Thread(target=schedule_loop, daemon=True)
    t.start()

# Punto de entrada de la aplicación
if __name__ == '__main__':
    # Al iniciar, programar las tareas y lanzar el hilo del scheduler
    schedule_jobs()
    start_scheduler()

    # Iniciar la app Flask
    app.run(debug=True, port=5000)
