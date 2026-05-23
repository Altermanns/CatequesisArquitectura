from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from pymongo import MongoClient
import json
import os
from dotenv import load_dotenv
from security import keycloak_manager, User

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'una_llave_secreta_para_flask')

# Configuración Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user_data = session.get('user')
    if user_data:
        return User(user_data['id'], user_data['name'], user_data['email'], user_data['roles'])
    return None

# Conexión a MongoDB (usando variable de entorno para flexibilidad)
mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongo:27017/Catequesis')
client = MongoClient(mongo_uri)
db = client.get_default_database() if 'srv' in mongo_uri else client['Catequesis']
catequistas = db['Catequista']
estudiantes = db['Estudiante']
grupos = db['Grupos']
sacramentos = db['Sacramentos']

@app.route('/login')
def login():
    # Forzamos 127.0.0.1 para que coincida exactamente con la configuración de Keycloak
    redirect_uri = url_for('callback', _external=True).replace('0.0.0.0', '127.0.0.1').replace('localhost', '127.0.0.1')
    return redirect(keycloak_manager.get_login_url(redirect_uri))

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Error: No code provided", 400
    
    redirect_uri = url_for('callback', _external=True).replace('0.0.0.0', '127.0.0.1').replace('localhost', '127.0.0.1')
    
    try:
        # Intercambiar código por token
        token = keycloak_manager.get_token(code, redirect_uri)
        # Obtener info del usuario
        user_info = keycloak_manager.get_user_info(token['access_token'])
        
        # Crear objeto de usuario
        user_obj = {
            'id': user_info['sub'],
            'name': user_info.get('preferred_username', user_info.get('name')),
            'email': user_info.get('email'),
            'roles': user_info.get('realm_access', {}).get('roles', [])
        }
        
        # Guardar en sesión y loguear
        session['user'] = user_obj
        user = User(user_obj['id'], user_obj['name'], user_obj['email'], user_obj['roles'])
        login_user(user)
        
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error en la autenticación: {str(e)}", 500

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user', None)
    redirect_uri = url_for('index', _external=True)
    return redirect(keycloak_manager.get_logout_url(redirect_uri))

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
