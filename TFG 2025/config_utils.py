import json
import logging
import os

CONFIG_FILE = 'config.json' 

def load_config():
    """Carga la configuración desde el archivo JSON."""
    try:
        with open(CONFIG_FILE, 'r') as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        logging.error("El archivo de configuración no existe.")
        return {}
    except Exception as e:
        logging.error(f"Error al cargar config.json: {e}")
        return {}

def save_config(config):
    """Guarda la configuración en el archivo JSON."""
    try:
        with open(CONFIG_FILE, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logging.info("Configuración guardada correctamente.")
    except PermissionError:
        logging.error(f"Permiso denegado: no se puede escribir en {CONFIG_FILE}.")
    except Exception as e:
        logging.error(f"Error al guardar config.json: {e}")



# Este fichero es para evitar bluces de importaciones, ya que estaba intentando importar tasks.py en scheduler.py y viceversa, cosa que me generaba errores. 