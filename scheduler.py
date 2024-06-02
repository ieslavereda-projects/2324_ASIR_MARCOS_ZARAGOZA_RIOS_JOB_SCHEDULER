#importar librerias
import schedule
import time
import logging
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import shutil
import os
import pyfiglet
import psutil
import subprocess
from datetime import datetime
import zipfile

# configuración de logs
logging.basicConfig(filename='scheduler.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# funcion para enviar el correo electrónico
def send_email(subject, body, attachment_path, config):
    try:
        # configuración del servidor SMTP, la cogemos del config.json
        smtp_server = config['email']['smtp_server']
        smtp_port = config['email']['smtp_port']
        username = config['email']['username']
        password = config['email']['password']
        from_addr = config['email']['from_addr']
        to_addrs = config['email']['to_addrs']

        # crear el mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # adjuntar el archivo de backup si existe
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(attachment_path)}")
                msg.attach(part)

        # conectar al servidor SMTP y enviar el correo
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.sendmail(from_addr, to_addrs, msg.as_string())
        server.quit()

        logging.info(f"Correo enviado a {to_addrs}")
        print(f"Correo enviado a {to_addrs}")

    except Exception as e:
        logging.error(f"Error al enviar correo: {e}")
        print(f"Error al enviar correo: {e}")


# funcion para realizar el backup de la carpeta
def backup_folder(source_folder, destination_folder):
    try:
        if os.path.exists(destination_folder):
            shutil.rmtree(destination_folder)
        shutil.copytree(source_folder, destination_folder)
        logging.info(f"Carpeta respaldada en {destination_folder}")
        print(f"Carpeta respaldada en {destination_folder}")
        return True
    except Exception as e:
        logging.error(f"Error al realizar el backup: {e}")
        print(f"Error al realizar el backup: {e}")
        return False


# funcion para comprimir la carpeta de backup
def compress_backup_folder(folder_path, zip_path):
    try:
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file), 
                               os.path.relpath(os.path.join(root, file), folder_path))
        logging.info(f"Carpeta comprimida en {zip_path}")
        print(f"Carpeta comprimida en {zip_path}")
        return True
    except Exception as e:
        logging.error(f"Error al comprimir el backup: {e}")
        print(f"Error al comprimir el backup: {e}")
        return False


# funcion para cargar la configuración desde config.json
def load_config():
    with open('config.json') as config_file:
        return json.load(config_file)


# DEFINICION DE TAREAS
def backup_and_send_email():
    logging.info("Job: Backup Automático y Envío de Correo Electrónico")
    print("Realizando backup y enviando correo...")

    source_folder = "/home/marcos/job_scheduler/prueba"  # ruta de la carpeta a respaldar
    destination_folder = "/home/marcos/job_scheduler/backup2"  # ruta de la carpeta de destino para el backup
    zip_path = "/home/marcos/job_scheduler/backup2.zip"  # ruta del archivo comprimido de backup

    # realizar el backup de la carpeta
    if backup_folder(source_folder, destination_folder):
        # comprimir la carpeta de backup
        if compress_backup_folder(destination_folder, zip_path):
            # enviar correo electronico con el archivo adjunto
            subject = "Backup Automático"
            body = "Se ha realizado el backup automático de la carpeta."
            config = load_config()  # cargar la configuración del correo
            send_email(subject, body, zip_path, config)


def get_logged_in_users():
    try:
        # obtener la lista de usuarios logeados
        logged_in_users = subprocess.check_output('who').decode('utf-8')
        return logged_in_users
    except Exception as e:
        logging.error(f"Error al obtener la lista de usuarios logeados: {e}")
        print(f"Error al obtener la lista de usuarios logeados: {e}")
        return ""


def get_logged_in_users_and_send_email():
    try:
        config = load_config()
        users = get_logged_in_users()
        subject = "Usuarios Logeados en el Sistema"
        body = f"Lista de usuarios logeados:\n{users}"
        send_email(subject, body, None, config)
    except Exception as e:
        logging.error(f"Error al enviar la lista de usuarios logeados: {e}")
        print(f"Error al enviar la lista de usuarios logeados: {e}")


def clean_trash():
    try:
        trash_dir = os.path.expanduser('~/.local/share/Trash/files')
        if os.path.exists(trash_dir):
            for filename in os.listdir(trash_dir):
                file_path = os.path.join(trash_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logging.error(f"Error al eliminar {file_path}: {e}")
                    print(f"Error al eliminar {file_path}: {e}")
            logging.info("Papelera limpiada")
            print("Papelera limpiada")
        else:
            logging.info("La carpeta de la papelera no existe")
            print("La carpeta de la papelera no existe")
    except Exception as e:
        logging.error(f"Error al limpiar la papelera: {e}")
        print(f"Error al limpiar la papelera: {e}")


# definir un diccionario para mapear nombres de tareas a funciones
task_functions = {
    'backup_and_send_email': backup_and_send_email,
    'get_logged_in_users_and_send_email': get_logged_in_users_and_send_email,
    'clean_trash': clean_trash
}


def schedule_jobs(config):
    logging.info("Programando tareas")
    for job in config['jobs']:
        logging.info(f"Programando {job['task']} cada {job['interval']}")
        task_function = task_functions.get(job['task'])
        if task_function and callable(task_function):
            if job['interval'] == 'daily':
                schedule.every().day.at(job['time']).do(task_function)
            elif job['interval'] == 'hourly':
                schedule.every().hour.at(f":{job['minute']}").do(task_function)
            elif job['interval'] == 'minute':
                schedule.every(job['minutes']).minutes.do(task_function)
        else:
            logging.error(f"No se encontró una función válida para la tarea: {job['task']}")

# menu
def display_menu():
    print("----------------- MENU DE INICIO -----------------")
    print("1. Definir job")
    print("2. Ejecutar jobs")
    print("3. Monitorizar uso de memoria y disco")
    print("4. Alerta de uso de memoria")
    print("5. Salir")


def display_task_menu():
    print("Selecciona el tipo de job:")
    print("1. Backup y envío de correo electrónico")
    print("2. Monitorización de usuarios logeados")
    print("3. Programar Limpieza de Papelera")


def define_job(config):
    display_task_menu()
    task_choice = input("Elige una opción de job: ")

    if task_choice == '1':
        task = 'backup_and_send_email' 
    elif task_choice == '2':
        task = 'get_logged_in_users_and_send_email'  # define el nuevo job para obtener 
    elif task_choice == '3':                         # la lista de usuarios y enviar el correo
        task = 'clean_trash'  # limpieza de papelera
    else:
        print("Opción de job no válida")
        return

    interval = input("Introduce el intervalo de ejecución (daily/hourly/minute): ")

    if interval == 'minute':
        minutes = int(input("Introduce el número de minutos: "))
        job = {"task": task, "interval": interval, "minutes": minutes}
    elif interval == 'hourly':
        minute = int(input("Introduce el minuto de la hora (0-59): "))
        job = {"task": task, "interval": interval, "minute": minute}
    elif interval == 'daily':
        time = input("Introduce la hora de ejecución diaria (HH:MM): ")
        job = {"task": task, "interval": interval, "time": time}
    else:
        print("Intervalo no válido")
        return

    config['jobs'].append(job)
    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)
    print("Job definido y guardado en config.json")


def monitor_memory_and_disk_usage():
    try:
        while True:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            logging.info(f"Uso de memoria: {memory.percent}%")
            logging.info(f"Uso de disco: {disk.percent}%")
            print(f"Uso de memoria: {memory.percent}%")
            print(f"Uso de disco: {disk.percent}%")
            time.sleep(60)
    except KeyboardInterrupt:
        print("Monitorización interrumpida")


def send_alert_email(subject, body, config):
    try:
        # configuracion servidor SMTP para envio de alertra
        smtp_server = config['email']['smtp_server']
        smtp_port = config['email']['smtp_port']
        username = config['email']['username']
        password = config['email']['password']
        from_addr = config['email']['from_addr']
        to_addrs = config['email']['to_addrs']

        # crear el mensaje de correo
        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # conectar al servidor SMTP y enviar el correo
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.sendmail(from_addr, to_addrs, msg.as_string())
        server.quit()

        logging.info(f"Correo de alerta enviado a {to_addrs}")
        print(f"Correo de alerta enviado a {to_addrs}")

    except Exception as e:
        logging.error(f"Error al enviar el correo de alerta: {e}")
        print(f"Error al enviar el correo de alerta: {e}")


def check_memory_usage_and_alert(config):
    try:
        # verifica si el umbral de alerta de memoria esta en la configuracion
        if 'memory_alert_threshold' not in config:
            # si no esta pregunta al usuario por el umbral
            memory_threshold = int(input("Introduce el umbral de alerta de memoria (en porcentaje): "))
            config['memory_alert_threshold'] = memory_threshold

            # guardar la configuracion actualizada en config.json
            with open('config.json', 'w') as config_file:
                json.dump(config, config_file, indent=4)
        else:
            # si esta obtener el umbral de la configuracion
            memory_threshold = config['memory_alert_threshold']

        # obtener el uso de memoria
        memory_usage = psutil.virtual_memory()
        memory_percent = memory_usage.percent

        # verificar si se supera el umbral de alerta
        if memory_percent > memory_threshold:
            subject = "Alerta de Uso de Memoria"
            body = f"El uso de memoria ha superado el umbral de {memory_threshold}%. Uso actual: {memory_percent}%."
            send_alert_email(subject, body, config)

    except Exception as e:
        logging.error(f"Error al verificar el uso de memoria: {e}")
        print(f"Error al verificar el uso de memoria: {e}")



def main():
    ascii_banner = pyfiglet.figlet_format("Job Scheduler")
    print(ascii_banner)
    print("Proyecto Final de Grado 2ASIR - Programado por Marcos Zaragoza")
    print("")

    # carga la configuracion desde config.json
    config = load_config()

    while True:
        display_menu()
        choice = input("Selecciona una opción: ")

        if choice == '1':
            define_job(config)
        elif choice == '2':
            schedule_jobs(config)
            print("Jobs programados. Presiona Ctrl+C para detener.")
            while True:
                schedule.run_pending()
                time.sleep(1)
        elif choice == '3':
            monitor_memory_and_disk_usage()
        elif choice == '4':
            check_memory_usage_and_alert(config)
        elif choice == '5':
            print("Saliendo...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")


if __name__ == "__main__":
    main()
