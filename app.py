from flask import Flask, request, jsonify, render_template
from models import db, Apuesta, Bankroll, MovimientoBankroll
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


@app.route('/')
def home():
    return render_template('index.html')


# ---------- CRUD de Apuestas ----------

@app.route('/api/apuestas', methods=['GET'])
def listar_apuestas():
    apuestas = Apuesta.query.order_by(Apuesta.fecha.desc()).all()
    return jsonify([{
        'id': a.id,
        'numero_apuesta': a.numero_apuesta,
        'fecha': a.fecha.strftime('%Y-%m-%d %H:%M'),
        'deporte': a.deporte,
        'tipo': a.tipo,
        'descripcion': a.descripcion,
        'monto': a.monto,
        'cuota': a.cuota,
        'estado': a.estado,
        'ganancia_perdida': a.ganancia_perdida
    } for a in apuestas])


@app.route('/api/apuestas', methods=['POST'])
def crear_apuesta():
    data = request.json

    nueva = Apuesta(
        numero_apuesta=data['numero_apuesta'],
        deporte=data['deporte'],
        tipo=data['tipo'],
        descripcion=data.get('descripcion', ''),
        monto=float(data['monto']),
        cuota=float(data['cuota']),
        estado='pendiente'
    )
    db.session.add(nueva)
    db.session.commit()

    return jsonify({'mensaje': 'Apuesta creada', 'id': nueva.id}), 201


@app.route('/api/apuestas/<int:id>', methods=['PUT'])
def editar_apuesta(id):
    apuesta = Apuesta.query.get_or_404(id)
    data = request.json

    apuesta.deporte = data.get('deporte', apuesta.deporte)
    apuesta.tipo = data.get('tipo', apuesta.tipo)
    apuesta.descripcion = data.get('descripcion', apuesta.descripcion)
    apuesta.monto = float(data.get('monto', apuesta.monto))
    apuesta.cuota = float(data.get('cuota', apuesta.cuota))

    db.session.commit()
    return jsonify({'mensaje': 'Apuesta actualizada'})


@app.route('/api/apuestas/<int:id>', methods=['DELETE'])
def eliminar_apuesta(id):
    apuesta = Apuesta.query.get_or_404(id)
    db.session.delete(apuesta)
    db.session.commit()
    return jsonify({'mensaje': 'Apuesta eliminada'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Crear el bankroll inicial si no existe
        if not Bankroll.query.first():
            db.session.add(Bankroll(monto_actual=0.0))
            db.session.commit()
    app.run(debug=True)