# Job Scheduler

Proyecto Final de Grado 2ASIR - Programado por Marcos Zaragoza

## Descripción

Este proyecto es un Job Scheduler (planificador de tareas) diseñado para ejecutar y gestionar varias tareas automatizadas, 
como realizar copias de seguridad de carpetas, enviar correos electrónicos, monitorizar el uso de memoria y limpiar la papelera del sistema.

## Características

- Backup y envío de correo electrónico: Realiza una copia de seguridad de una carpeta específica y envía un correo electrónico con el archivo de backup adjunto.
- Monitorización de usuarios logeados: Envía un correo electrónico con la lista de usuarios actualmente logeados en el sistema.
- Limpieza de papelera: Limpia automáticamente la papelera del sistema.
- Alerta de uso de memoria: Envía un correo electrónico de alerta cuando el uso de memoria supera un umbral definido.

## Requisitos

- Python 3.12
- Las siguientes librerías de Python:
  - schedule
  - psutil
  - pyfiglet

## Instalación

1. Clonar el repositorio:

    git clone https://github.com/ieslavereda-projects/2324_ASIR_MARCOS_ZARAGOZA_RIOS_JOB_SCHEDULER.git
    cd job_scheduler
    

2. Instalar las dependencias:

    pip install -r requirements.txt
    

3. Configurar el archivo config.json:

    Edita el archivo config.json y configura los parámetros según tus necesidades, 
    incluyendo la configuración del servidor SMTP para enviar correos electrónicos.


    {
        "email": {
            "smtp_server": "smtp.ejemplo.com",
            "smtp_port": 587,
            "username": "tu_usuario",
            "password": "tu_contraseña",
            "from_addr": "tu_correo@ejemplo.com",
            "to_addrs": ["destinatario1@ejemplo.com", "destinatario2@ejemplo.com"]
        },

        "jobs": []
    }
    

4. Ejecutar el programa:

    python scheduler.py
    

## Uso

### Menú principal

1. Definir job: Permite definir y programar nuevas tareas.
2. Ejecutar jobs: Inicia la ejecución de las tareas programadas.
3. Monitorizar uso de memoria y disco: Muestra el uso actual de memoria y disco en intervalos regulares.
4. Alerta de uso de memoria: Comprueba el uso de memoria y envía una alerta si supera el umbral definido.
5. Salir: Cierra el programa.

### Definición de jobs

Para definir un nuevo job, selecciona la opción "1. Definir job" en el menú principal y
sigue las instrucciones para especificar el tipo de tarea y el intervalo de ejecución.


## Contacto

Para cualquier consulta o sugerencia, por favor contacta a [tfgmarcosz@gmail.com]



## Solución de Problemas Comunes

Error al enviar correo: Verifique la configuración SMTP en config.json y asegúrese de que las credenciales y los servidores sean correctos.

Tarea no se ejecuta a la hora programada: Revise el archivo de log para identificar posibles errores y asegúrese de que el sistema esté en ejecución.

Uso de memoria alto sin alerta: Asegúrese de que el umbral de alerta esté correctamente configurado en config.json y que la opción 4 se haya ejecutado.

Este manual de usuario debe proporcionar toda la información necesaria para utilizar eficazmente el Job Scheduler. Si tiene preguntas adicionales 
o necesita asistencia técnica, consulte la documentación adicional o comuníquese con el correo de soporte tfgmarcosz@gmail.com.
