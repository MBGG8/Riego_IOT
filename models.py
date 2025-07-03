
from database import db
from datetime import datetime

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temperatura = db.Column(db.Float)
    humedad_suelo = db.Column(db.Float)
    humedad_ambiental = db.Column(db.Float)
    luminosidad = db.Column(db.Float)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class RiegoEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activar = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class SistemaEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activo = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

class RiegoManual(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activar = db.Column(db.Boolean, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

# --- NUEVO: persistir flag automático ---
class RiegoConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    auto = db.Column(db.Boolean, nullable=False, default=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
