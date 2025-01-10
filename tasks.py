import os
import shutil
import smtplib
import logging
import subprocess
import zipfile
import paramiko
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from config_utils import load_config, save_config  # Importar desde config_utils.py

logging.basicConfig(
    filename='scheduler.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def send_email(subject, body, attachment_path, config):
    """Envía un correo electrónico usando la configuración (SMTP) de config.json."""
    try:
        smtp_server = config['email']['smtp_server']
        smtp_port   = config['email']['smtp_port']
        username    = config['email']['username']
        password    = config['email']['password']
        from_addr   = config['email']['from_addr']
        to_addrs    = config['email']['to_addrs']

        msg = MIMEMultipart()
        msg['From'] = from_addr
        msg['To']   = ", ".join(to_addrs)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Adjuntar archivo si procede
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f"attachment; filename= {os.path.basename(attachment_path)}"
                )
                msg.attach(part)

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



# Configurar logging SFTP
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



# Parámetros de configuración para conexión SFTP
SFTP_HOST = '192.168.1.66'        
SFTP_PORT = 22                           
SFTP_USERNAME = 'backupuser'              
SFTP_PASSWORD = '1234'     

# Ruta en el servidor SFTP donde se almacenarán los respaldos
SFTP_REMOTE_PATH = '/home/backupuser/backup/backup.zip'

# Ruta local del archivo de respaldo
LOCAL_BACKUP_FILE = '/home/marcos/backup/backup.zip'


# Creación y compresión del backup
def create_backup(source_dir, backup_file):
    try:
        backup_dir = os.path.dirname(backup_file)
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            logging.info(f"Directorio creado: {backup_dir}")
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            for foldername, subfolders, filenames in os.walk(source_dir):
                for filename in filenames:
                    file_path = os.path.join(foldername, filename)
                    backup_zip.write(file_path, arcname=os.path.relpath(file_path, source_dir))
        logging.info(f"Respaldo creado exitosamente en {backup_file}")
    except Exception as e:
        logging.error(f"Error al crear el respaldo: {e}")
        raise


def transfer_to_sftp(local_file, remote_path):
    try:
        # Verificar si el archivo local existe
        if not os.path.isfile(local_file):
            logging.error(f"El archivo local {local_file} no existe.")
            raise FileNotFoundError(f"El archivo local {local_file} no existe.")

        # Crear un cliente SSH
        transport = paramiko.Transport((SFTP_HOST, SFTP_PORT))
        
        # Autenticación con contraseña
        transport.connect(username=SFTP_USERNAME, password=SFTP_PASSWORD)
   
        # Crear un cliente SFTP
        sftp = paramiko.SFTPClient.from_transport(transport)
        
        # Transferir el archivo
        sftp.put(local_file, remote_path)
        logging.info(f"Archivo transferido exitosamente a {remote_path}")
        
        # Cerrar la conexión SFTP
        sftp.close()
        transport.close()
        
    except paramiko.AuthenticationException:
        logging.error("Autenticación fallida al conectar con el servidor SFTP.")
        raise
    except paramiko.SSHException as sshException:
        logging.error(f"Error de conexión SSH: {sshException}")
        raise
    except FileNotFoundError as fnf_error:
        logging.error(f"Error al transferir el archivo: {fnf_error}")
        raise
    except Exception as e:
        logging.error(f"Error al transferir el archivo: {e}")
        raise



# Respaldo y transferencia
def backup_and_transfer():
    SOURCE_DIRECTORY = '/home/marcos/prueba'      # Directorio que deseas respaldar
    try:
        # Paso 1: Crear el respaldo
        create_backup(SOURCE_DIRECTORY, LOCAL_BACKUP_FILE)
        
        # Paso 2: Transferir el respaldo al servidor SFTP
        transfer_to_sftp(LOCAL_BACKUP_FILE, SFTP_REMOTE_PATH)
        
        logging.info("Tarea de respaldo y transferencia completada exitosamente.")
    except Exception as e:
        logging.error(f"Fallo en la tarea de respaldo y transferencia: {e}")




def get_logged_in_users():
    """Devuelve la lista de usuarios logeados (comando who)."""
    try:
        logged_in_users = subprocess.check_output('who').decode('utf-8')
        return logged_in_users
    except Exception as e:
        logging.error(f"Error al obtener usuarios logeados: {e}")
        print(f"Error al obtener usuarios logeados: {e}")
        return ""

def get_logged_in_users_and_send_email():
    """Ejemplo de tarea: obtiene lista de usuarios y la envía por correo."""
    logging.info("Job: Usuarios Logeados + Email")
    print("Obteniendo usuarios y enviando correo...")

    try:
        config = load_config()
        users  = get_logged_in_users()
        subject = "Usuarios Logeados en el Sistema"
        body    = f"Lista de usuarios logeados:\n{users}"
        send_email(subject, body, None, config)

        # Actualizar last_execution
        config['last_execution'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_config(config)
    except Exception as e:
        logging.error(f"Error en get_logged_in_users_and_send_email: {e}")
        print(f"Error en get_logged_in_users_and_send_email: {e}")

def clean_trash():
    """Limpia la papelera local."""
    logging.info("Job: Limpiar Papelera")
    print("Limpiando papelera...")

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

            # Actualizar last_execution
            config = load_config()
            config['last_execution'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_config(config)
        else:
            logging.info("La carpeta de la papelera no existe")
            print("La carpeta de la papelera no existe")
    except Exception as e:
        logging.error(f"Error al limpiar la papelera: {e}")
        print(f"Error al limpiar la papelera: {e}")

# Mapa de nombres de tarea en config.json -> Funciones Python
task_functions = {
    'backup_and_transfer': backup_and_transfer,
    'get_logged_in_users_and_send_email': get_logged_in_users_and_send_email,
    'clean_trash': clean_trash
}

# Diccionario que mapea el nombre de la tarea con su descripción
task_descriptions = {
    'backup_and_transfer': 'Realiza una copia de seguridad y la envía a través de un servidor seguro SFTP.',
    'get_logged_in_users_and_send_email': 'Obtiene la lista de usuarios actualmente conectados y envía un correo electrónico.',
    'clean_trash': 'Limpia la papelera de reciclaje eliminando archivos antiguos.'
}


