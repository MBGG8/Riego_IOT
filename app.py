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
    activar = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def nocache_json(data, status=200):
    resp = make_response(jsonify(data), status)
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

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

# Devuelve el override (estado del botón)
@app.route('/estado', methods=['GET'])
def estado():
    ultimo = RiegoEstado.query.order_by(RiegoEstado.fecha.desc()).first()
    return nocache_json({"activar": bool(ultimo.activar) if ultimo else False})

# Cambia override desde el dashboard
@app.route('/riego', methods=['POST'])
def riego():
    data = request.get_json(force=True)
    if 'activar' not in data:
        return nocache_json({"error": "Falta 'activar'"}, 400)
    estado = bool(data['activar'])
    re = RiegoEstado(activar=estado)
    db.session.add(re)
    db.session.commit()
    return nocache_json({"status": "override actualizado", "activar": estado})

# Últimos datos para la card
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

# Histórico para gráficas
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

@app.route('/historiaIOT')
def historia_iot():
     # Definir la zona horaria de Lima
    zona_lima = pytz.timezone('America/Lima')
 
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

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
