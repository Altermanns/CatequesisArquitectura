from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
BACKEND = 'http://localhost:5000'  # Asegúrate que el backend esté corriendo aquí

# ---------------------- HOME ----------------------

@app.route('/')
def home():
    return jsonify({"mensaje": "Middleware REST operativo"}), 200

# ---------------------- CATEQUISTAS ----------------------

@app.route('/api/catequistas', methods=['GET'])
def listar_catequistas():
    res = requests.get(f'{BACKEND}/catequistas')
    return res.content, res.status_code, res.headers.items()

@app.route('/api/catequistas/agregar', methods=['POST'])
def agregar_catequista():
    res = requests.post(f'{BACKEND}/catequistas/agregar', data=request.form)
    return jsonify({"mensaje": "Catequista agregado"}), 200 if res.status_code == 302 else res.status_code

@app.route('/api/catequistas/editar/<id>', methods=['POST'])
def editar_catequista(id):
    res = requests.post(f'{BACKEND}/catequistas/editar/{id}', data=request.form)
    return jsonify({"mensaje": "Catequista actualizado"}), 200 if res.status_code == 302 else res.status_code

@app.route('/api/catequistas/eliminar/<id>', methods=['GET'])
def eliminar_catequista(id):
    res = requests.get(f'{BACKEND}/catequistas/eliminar/{id}')
    return jsonify({"mensaje": "Catequista eliminado"}), 200 if res.status_code == 302 else res.status_code

@app.route('/api/catequistas/buscar', methods=['GET'])
def buscar_catequistas():
    termino = request.args.get('termino', '')
    res = requests.get(f'{BACKEND}/catequistas/buscar', params={'termino': termino})
    return res.content, res.status_code, res.headers.items()

# ---------------------- ESTUDIANTES ----------------------

@app.route('/api/estudiantes', methods=['GET'])
def listar_estudiantes():
    res = requests.get(f'{BACKEND}/estudiantes')
    return res.content, res.status_code, res.headers.items()

@app.route('/api/estudiantes/agregar', methods=['POST'])
def agregar_estudiante():
    # Construir datos correctamente para sacramentos
    data = request.form.to_dict()
    data['sacramentos'] = request.form.getlist('sacramentos')
    
    res = requests.post(f'{BACKEND}/estudiantes/agregar', data=data)
    return jsonify({"mensaje": "Estudiante agregado"}), 200 if res.status_code == 302 else res.status_code

@app.route('/api/estudiantes/editar/<id>', methods=['POST'])
def editar_estudiante(id):
    # Construir datos correctamente para sacramentos
    data = request.form.to_dict()
    data['sacramentos'] = request.form.getlist('sacramentos')
    
    res = requests.post(f'{BACKEND}/estudiantes/editar/{id}', data=data)
    return jsonify({"mensaje": "Estudiante actualizado"}), 200 if res.status_code == 302 else res.status_code

@app.route('/api/estudiantes/eliminar/<id>', methods=['GET'])
def eliminar_estudiante(id):
    res = requests.get(f'{BACKEND}/estudiantes/eliminar/{id}')
    return jsonify({"mensaje": "Estudiante eliminado"}), 200 if res.status_code == 302 else res.status_code

@app.route('/api/estudiantes/buscar', methods=['GET'])
def buscar_estudiantes():
    termino = request.args.get('termino', '')
    res = requests.get(f'{BACKEND}/estudiantes/buscar', params={'termino': termino})
    return res.content, res.status_code, res.headers.items()

# ---------------------- GRUPOS Y SACRAMENTOS ----------------------

@app.route('/api/grupos', methods=['GET'])
def listar_grupos():
    res = requests.get(f'{BACKEND}/grupos')
    return res.content, res.status_code, res.headers.items()

@app.route('/api/sacramentos', methods=['GET'])
def listar_sacramentos():
    res = requests.get(f'{BACKEND}/sacramentos')
    return res.content, res.status_code, res.headers.items()

# ---------------------- EJECUCIÓN ----------------------

if __name__ == '__main__':
    app.run(port=5003, debug=True)