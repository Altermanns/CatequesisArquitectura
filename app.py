from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import pika
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Conexión a MongoDB (local o contenedor docker)
client = MongoClient('mongodb+srv://matias:matias@cluster0.tb41iw7.mongodb.net/')
db = client['Catequesis']
catequistas = db['Catequista']
estudiantes = db['Estudiante']
grupos = db['Grupos']
sacramentos = db['Sacramentos']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/catequistas')
def listar_catequistas():
    lista = list(catequistas.find())
    return render_template('catequistas.html', catequistas=lista)

@app.route('/catequistas/agregar', methods=['POST'])
def agregar_catequista():
    data = {
        "_id": request.form['idCatequista'],
        "nombre": request.form['nombre'],
        "apellido": request.form['apellido'],
        "email": request.form['email'],
        "telefono": request.form['telefono'],
        "nivel": request.form['nivel'],
        "estado": "Activo",
        "grupos_asignados": []
    }
    catequistas.insert_one(data)
    return redirect(url_for('listar_catequistas'))

@app.route('/catequistas/editar/<id>', methods=['GET', 'POST'])
def editar_catequista(id):
    if request.method == 'POST':
        catequistas.update_one({"_id": id}, {"$set": {
            "nombre": request.form['nombre'],
            "apellido": request.form['apellido'],
            "nivel": request.form['nivel'],
            "email": request.form['email'],
            "telefono": request.form['telefono']
        }})
        return redirect(url_for('listar_catequistas'))
    catequista = catequistas.find_one({"_id": id})
    return render_template('editar_catequista.html', catequista=catequista)

@app.route('/catequistas/eliminar/<id>')
def eliminar_catequista(id):
    catequistas.delete_one({"_id": id})
    return redirect(url_for('listar_catequistas'))

@app.route('/catequistas/buscar')
def buscar_catequista():
    termino = request.args.get('termino', '')
    resultados = list(catequistas.find({"nombre": {"$regex": termino, "$options": "i"}}))
    return render_template('catequistas.html', catequistas=resultados)

@app.route('/estudiantes')
def listar_estudiantes():
    lista = list(estudiantes.find())
    lista_sacramentos = list(sacramentos.find())
    return render_template('estudiantes.html', estudiantes=lista, sacramentos=lista_sacramentos)

@app.route('/estudiantes/agregar', methods=['POST'])
def agregar_estudiante():
    sacramentos_faltantes = request.form.getlist('sacramentos')
    data = {
        "_id": request.form['idEstudiante'],
        "nombre": request.form['nombre'],
        "apellido": request.form['apellido'],
        "edad": int(request.form['edad']),
        "estado": "Activo",
        "grupo_id": request.form['grupoId'],
        "sacramentos": sacramentos_faltantes,
        "padres": [{
            "nombre": request.form['nombrePadre'],
            "telefono": request.form['telefonoPadre'],
            "email": request.form['emailPadre']
        }]
    }
    estudiantes.insert_one(data)

    # Enviar mensaje a RabbitMQ para correo de confirmación
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=os.getenv('RABBITMQ_HOST', 'rabbitmq')))
        channel = connection.channel()
        channel.queue_declare(queue='email_queue', durable=True)

        mensaje = {
            "nombre": data["nombre"],
            "apellido": data["apellido"],
            "email_padre": data["padres"][0]["email"]
        }

        channel.basic_publish(
            exchange='',
            routing_key='email_queue',
            body=json.dumps(mensaje),
            properties=pika.BasicProperties(delivery_mode=2)  # mensaje persistente
        )

        connection.close()
    except Exception as e:
        print("❌ Error al enviar a RabbitMQ:", e)

    return redirect(url_for('listar_estudiantes'))

@app.route('/estudiantes/editar/<id>', methods=['GET', 'POST'])
def editar_estudiante(id):
    if request.method == 'POST':
        estudiantes.update_one({"_id": id}, {"$set": {
            "nombre": request.form['nombre'],
            "apellido": request.form['apellido'],
            "edad": int(request.form['edad']),
            "grupo_id": request.form['grupoId'],
            "sacramentos": request.form.getlist('sacramentos'),
            "padres": [{
                "nombre": request.form['nombrePadre'],
                "telefono": request.form['telefonoPadre'],
                "email": request.form['emailPadre']
            }]
        }})
        return redirect(url_for('listar_estudiantes'))
    estudiante = estudiantes.find_one({"_id": id})
    lista_sacramentos = list(sacramentos.find())
    return render_template('editar_estudiante.html', estudiante=estudiante, sacramentos=lista_sacramentos)

@app.route('/estudiantes/eliminar/<id>')
def eliminar_estudiante(id):
    estudiantes.delete_one({"_id": id})
    return redirect(url_for('listar_estudiantes'))

@app.route('/estudiantes/buscar')
def buscar_estudiante():
    termino = request.args.get('termino', '')
    resultados = list(estudiantes.find({"nombre": {"$regex": termino, "$options": "i"}}))
    lista_sacramentos = list(sacramentos.find())
    return render_template('estudiantes.html', estudiantes=resultados, sacramentos=lista_sacramentos)

@app.route('/grupos')
def listar_grupos():
    lista = list(grupos.find())
    return render_template('grupos.html', grupos=lista)

@app.route('/sacramentos')
def listar_sacramentos():
    lista = list(sacramentos.find())
    return render_template('sacramentos.html', sacramentos=lista)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
