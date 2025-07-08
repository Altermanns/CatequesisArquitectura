import pika
import json
import smtplib
import os
import time
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

MAIL_SERVER = os.getenv('SMTP_SERVER')
MAIL_PORT = int(os.getenv('SMTP_PORT', 587))
MAIL_USERNAME = os.getenv('SMTP_USER')
MAIL_PASSWORD = os.getenv('SMTP_PASSWORD')
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@catequesis.local")
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False') == 'True'

def enviar_correo(destinatario, asunto, cuerpo):
    msg = MIMEText(cuerpo)
    msg['Subject'] = asunto
    msg['From'] = FROM_EMAIL
    msg['To'] = destinatario

    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as servidor:
        if MAIL_USE_TLS:
            servidor.starttls()
        servidor.login(MAIL_USERNAME, MAIL_PASSWORD)
        servidor.send_message(msg)
        print(f"✅ Correo enviado a {destinatario}")

def callback(ch, method, properties, body):
    try:
        print("📩 Mensaje recibido:", body)
        datos = json.loads(body)
        asunto = "Confirmación de inscripción a catequesis"
        cuerpo = f"""
Estimado padre/madre,

Su hijo(a) {datos['nombre']} {datos['apellido']} ha sido inscrito exitosamente al programa de catequesis.

Muchas gracias por su confianza.

Bendiciones,
Equipo de Catequesis
"""
        enviar_correo(datos['email_padre'], asunto, cuerpo)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print("❌ Error procesando el mensaje:", e)

def iniciar_worker():
    for intento in range(10):
        try:
            print(f"🔁 Intentando conectar a RabbitMQ (intento {intento+1})...")
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'rabbitmq'))
            )
            channel = connection.channel()
            channel.queue_declare(queue='email_queue', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='email_queue', on_message_callback=callback)
            print("📨 Esperando mensajes para enviar correos...")
            channel.start_consuming()
            break
        except pika.exceptions.AMQPConnectionError as e:
            print("⏳ RabbitMQ no disponible. Reintentando en 5 segundos...")
            time.sleep(5)
        except Exception as e:
            print("❌ Error inesperado:", e)
            break

if __name__ == "__main__":
    iniciar_worker()
