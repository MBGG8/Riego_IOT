import logging
from flask import Flask, request, jsonify, make_response, render_template
from datetime import datetime
import pytz
from database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///riego.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar DB
db.init_app(app)
zona_lima = pytz.timezone('America/Lima')

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float, nullable=True)
    humedad_suelo = db.Column(db.Float, nullable=True)
    humedad_ambiental = db.Column(db.Float, nullable=True)
    luminosidad = db.Column(db.Float, nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class RiegoEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activar = db.Column(db.Boolean, nullable=False)  # Estado del riego (activo/inactivo)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class SistemaEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activo = db.Column(db.Boolean, nullable=False)  # Activar o desactivar sistema
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()
    # Asegurar que haya un estado inicial del sistema
    if SistemaEstado.query.first() is None:
        estado_inicial = SistemaEstado(activo=False)
        db.session.add(estado_inicial)
        db.session.commit()

# Utilidad: JSON sin caché
def nocache_json(data, status=200):
    resp = make_response(jsonify(data), status)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

# Página principal
@app.route('/')
def index():
    return render_template('dashboard.html')

# Recibe datos del ESP32
@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()
    if not data:
        return nocache_json({"error": "No JSON recibido"}, 400)
    try:
        sd = SensorData(
            temperatura=data.get('temperatura'),
            humedad_suelo=data.get('humedad_suelo'),
            humedad_ambiental=data.get('humedad_ambiental'),
            luminosidad=data.get('luminosidad')
        )
        re = RiegoEstado(activar=(data.get('activaciones', 0) == 1))
        db.session.add(sd)
        db.session.add(re)
        db.session.commit()
        return nocache_json({"status": "ok"})
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return nocache_json({"error": str(e)}, 500)

# Últimos datos para el dashboard
@app.route('/data', methods=['GET'])
def get_data():
    ultimo = SensorData.query.order_by(SensorData.fecha.desc()).first()
    if not ultimo:
        return nocache_json({}, 200)
    return nocache_json({
        "temperatura": ultimo.temperatura,
        "humedad_suelo": ultimo.humedad_suelo,
        "humedad_ambiental": ultimo.humedad_ambiental,
        "luminosidad": ultimo.luminosidad
    })

# Histórico de sensores para gráficas
@app.route('/historico', methods=['GET'])
def historico():
    regs = SensorData.query.order_by(SensorData.fecha.desc()).limit(100).all()
    regs.reverse()
    out = []
    for r in regs:
        utc = r.fecha.replace(tzinfo=pytz.utc)
        lima = utc.astimezone(zona_lima).strftime("%Y-%m-%d %H:%M:%S")
        out.append({
            "timestamp": lima,
            "temperatura": r.temperatura,
            "humedad_suelo": r.humedad_suelo,
            "humedad_ambiental": r.humedad_ambiental,
            "luminosidad": r.luminosidad
        })
    return nocache_json(out)

# Página de historial
@app.route('/historiaIOT')
def historia_iot():
    return render_template('historia.html')

@app.route('/historiaIOT/json')
def historia_iot_json():
    registros_utc = SensorData.query.order_by(SensorData.fecha.desc()).limit(5000).all()
    registros = []
    for r in registros_utc:
        fecha_utc = r.fecha.replace(tzinfo=pytz.utc)
        fecha_lima = fecha_utc.astimezone(zona_lima)
        registros.append({
            'fecha': fecha_lima.strftime('%Y-%m-%d %H:%M:%S'),
            'temperatura': r.temperatura,
            'humedad_suelo': r.humedad_suelo,
            'humedad_ambiental': r.humedad_ambiental,
            'luminosidad': r.luminosidad
        })
    return jsonify(registros)

# 🔁 Estado actual del riego (para frontend)
@app.route('/estado', methods=['GET'])
def estado():
    ultimo = RiegoEstado.query.order_by(RiegoEstado.fecha.desc()).first()
    return nocache_json({"activar": bool(ultimo.activar) if ultimo else False})

# 🔁 Estado actual del sistema (para ESP32 y frontend)
@app.route('/sistema', methods=['GET'])
def get_sistema():
    ultimo = SistemaEstado.query.order_by(SistemaEstado.fecha.desc()).first()
    return nocache_json({"activo": bool(ultimo.activo) if ultimo else False})

# 🔁 Cambiar estado del sistema desde el dashboard
@app.route('/sistema', methods=['POST'])
def set_sistema():
    data = request.get_json(force=True)
    if 'activo' not in data:
        return nocache_json({"error": "Falta 'activo'"}, 400)
    nuevo_estado = bool(data['activo'])
    nuevo = SistemaEstado(activo=nuevo_estado)
    db.session.add(nuevo)
    db.session.commit()
    return nocache_json({"status": "estado sistema actualizado", "activo": nuevo_estado})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
