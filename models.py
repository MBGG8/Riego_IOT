from database import db
from datetime import datetime

class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sensor1 = db.Column(db.Float)
    sensor2 = db.Column(db.Float)
    sensor3 = db.Column(db.Float)
    sensor4 = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class RiegoEstado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    activar = db.Column(db.Boolean)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
