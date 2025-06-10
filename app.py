import logging
from flask import Flask, request, jsonify, make_response, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from database import db
import pytz
import os

app = Flask(__name__)

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///riego.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

zona_lima = pytz.timezone('America/Lima')

db.init_app(app)

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float, nullable=True)
    humedad_suelo = db.Column(db.Float, nullable=True)
    humedad_ambiental = db.Column(db.Float, nullable=True)
    luminosidad = db.Column(db.Float, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class RiegoEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activar = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# Inicializar la BD si no existe (opcional, si no lo haces en otro lado)
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    response = make_response(render_template('dashboard.html'))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def nocache_json_response(data):
    """Helper para respuesta JSON con headers anti-cache"""
    response = make_response(jsonify(data))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/historico', methods=['GET'])
def historico():
    zona_lima = pytz.timezone('America/Lima')
    # Obtener últimos 100 registros ordenados de forma descendente (más recientes primero)
    registros = SensorData.query.order_by(SensorData.fecha.desc()).limit(100).all()
    datos = []
    # Para mostrar cronológicamente los datos (de más antiguo a más reciente)
    registros.reverse()
    for r in registros:
        fecha_utc = r.fecha.replace(tzinfo=pytz.utc)  # Asumimos UTC
        fecha_lima = fecha_utc.astimezone(zona_lima)
        datos.append({
            "timestamp": fecha_lima.strftime("%Y-%m-%d %H:%M:%S"),
            "temperatura": r.temperatura,
            "humedad_suelo": r.humedad_suelo,
            "humedad_ambiental": r.humedad_ambiental,
            "luminosidad": r.luminosidad
        })
    return nocache_json_response(datos)

@app.route('/update', methods=['POST'])
def update_data():
    data = request.json
    if not data:
        return nocache_json_response({"error": "No se recibieron datos JSON"}), 400
    sensor = SensorData(
        temperatura=data.get('temperatura'),
        humedad_suelo=data.get('humedad_suelo'),
        humedad_ambiental=data.get('humedad_ambiental'),
        luminosidad=data.get('luminosidad')
    )
    db.session.add(sensor)
    db.session.commit()
    return nocache_json_response({"status": "ok"}), 200

@app.route('/data', methods=['GET'])
def get_data():
    ultimo = SensorData.query.order_by(SensorData.fecha.desc()).first()
    if ultimo:
        return nocache_json_response({
            "temperatura": ultimo.temperatura,
            "humedad_suelo": ultimo.humedad_suelo,
            "humedad_ambiental": ultimo.humedad_ambiental,
            "luminosidad": ultimo.luminosidad,
            "fecha": ultimo.fecha.isoformat()
        })
    return nocache_json_response({}), 200

@app.route('/historiaIOT')
def historia_iot():
     # Traemos todos los registros ordenados de más nuevo a más antiguo
    registros_utc = SensorData.query.order_by(SensorData.fecha.desc()).all()

    # Convertimos cada fecha UTC a Lima
    registros = []
    for r in registros_utc:
        # Asumimos que r.fecha es naive en UTC
        fecha_utc = r.fecha.replace(tzinfo=pytz.utc)
        fecha_lima = fecha_utc.astimezone(zona_lima)
        registros.append({
            'fecha': fecha_lima,  # un datetime ya en Lima
            'temperatura': r.temperatura,
            'humedad_suelo': r.humedad_suelo,
            'humedad_ambiental': r.humedad_ambiental,
            'luminosidad': r.luminosidad
        })

    # Renderizamos pasando la lista con datetimes de Lima
    return render_template('historia.html', registros=registros)

@app.route('/riego', methods=['POST'])
def riego():
    data = request.get_json(force=True)
    estado = data.get('activar')
    if estado is None:
        return nocache_json_response({"error": "Falta clave 'activar' en JSON"}), 400
    nuevo_estado = RiegoEstado(activar=bool(estado))
    db.session.add(nuevo_estado)
    db.session.commit()
    return nocache_json_response({"status": "riego actualizado", "activar": estado})

@app.route('/estado', methods=['GET'])
def estado_riego():
    ultimo_estado = RiegoEstado.query.order_by(RiegoEstado.fecha.desc()).first()
    if ultimo_estado:
        return nocache_json_response({"activar": ultimo_estado.activar})
    return nocache_json_response({"activar": False})


@app.route('/toggle-riego', methods=['POST'])
def toggle_riego():
    from models import Estado  # Asegúrate que esté correctamente importado

    estado = Estado.query.order_by(Estado.id.desc()).first()
    if estado:
        estado.activar = not estado.activar
        db.session.commit()
        return jsonify({'activar': estado.activar})
    return jsonify({'activar': False}), 404

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
