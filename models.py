from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Bankroll(db.Model):
    __tablename__ = 'bankroll'

    id = db.Column(db.Integer, primary_key=True)
    monto_actual = db.Column(db.Float, nullable=False, default=0.0)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Bankroll ${self.monto_actual}>'


class Apuesta(db.Model):
    __tablename__ = 'apuestas'

    id = db.Column(db.Integer, primary_key=True)
    numero_apuesta = db.Column(db.String(20), unique=True, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    deporte = db.Column(db.String(50), nullable=False)  # futbol, futbol_americano, otro
    tipo = db.Column(db.String(20), nullable=False)      # sencilla, parlay
    descripcion = db.Column(db.String(255))
    monto = db.Column(db.Float, nullable=False)
    cuota = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente, ganada, perdida
    ganancia_perdida = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<Apuesta {self.numero_apuesta} - {self.deporte}>'


class MovimientoBankroll(db.Model):
    __tablename__ = 'movimientos_bankroll'

    id = db.Column(db.Integer, primary_key=True)
    apuesta_id = db.Column(db.Integer, db.ForeignKey('apuestas.id'), nullable=True)
    monto_cambio = db.Column(db.Float, nullable=False)  # positivo o negativo
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    saldo_resultante = db.Column(db.Float, nullable=False)
    descripcion = db.Column(db.String(255))  # ej. "Ganancia apuesta #12" o "Depósito manual"

    apuesta = db.relationship('Apuesta', backref='movimiento')

    def __repr__(self):
        return f'<Movimiento ${self.monto_cambio}>'