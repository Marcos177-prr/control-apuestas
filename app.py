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

@app.route('/api/apuestas/<numero_apuesta>', methods=['PUT'])
def editar_apuesta(numero_apuesta):
    apuesta = Apuesta.query.filter_by(numero_apuesta=numero_apuesta).first_or_404()
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


@app.route('/api/apuestas/<numero_apuesta>/resolver', methods=['POST'])
def resolver_apuesta(numero_apuesta):
    apuesta = Apuesta.query.filter_by(numero_apuesta=numero_apuesta).first_or_404()
    data = request.json
    resultado = data.get('resultado')  # 'ganada' o 'perdida'

    if apuesta.estado != 'pendiente':
        return jsonify({'error': 'Esta apuesta ya fue resuelta'}), 400

    if resultado not in ['ganada', 'perdida']:
        return jsonify({'error': 'Resultado inválido'}), 400

    bankroll = Bankroll.query.first()

    if resultado == 'ganada':
        # Ganancia neta = lo que arriesgaste * (cuota - 1)
        ganancia = round(apuesta.monto * (apuesta.cuota - 1), 2)
        apuesta.ganancia_perdida = ganancia
        bankroll.monto_actual += (apuesta.monto + ganancia)  # se devuelve el monto apostado + la ganancia
        descripcion_mov = f'Ganancia apuesta #{apuesta.numero_apuesta}'
        cambio = apuesta.monto + ganancia

    else:  # perdida
        apuesta.ganancia_perdida = -apuesta.monto
        bankroll.monto_actual -= apuesta.monto
        descripcion_mov = f'Pérdida apuesta #{apuesta.numero_apuesta}'
        cambio = -apuesta.monto

    apuesta.estado = resultado

    movimiento = MovimientoBankroll(
        apuesta_id=apuesta.id,
        monto_cambio=cambio,
        saldo_resultante=bankroll.monto_actual,
        descripcion=descripcion_mov
    )
    db.session.add(movimiento)
    db.session.commit()

    return jsonify({
        'mensaje': f'Apuesta marcada como {resultado}',
        'ganancia_perdida': apuesta.ganancia_perdida,
        'bankroll_actual': bankroll.monto_actual
    })
@app.route('/api/bankroll', methods=['GET'])
def ver_bankroll():
    bankroll = Bankroll.query.first()
    movimientos = MovimientoBankroll.query.order_by(MovimientoBankroll.fecha.desc()).limit(20).all()

    return jsonify({
        'monto_actual': bankroll.monto_actual,
        'movimientos': [{
            'fecha': m.fecha.strftime('%Y-%m-%d %H:%M'),
            'monto_cambio': m.monto_cambio,
            'saldo_resultante': m.saldo_resultante,
            'descripcion': m.descripcion
        } for m in movimientos]
    })


@app.route('/api/bankroll/deposito', methods=['POST'])
def depositar_bankroll():
    data = request.json
    monto = float(data.get('monto', 0))

    if monto <= 0:
        return jsonify({'error': 'El monto debe ser mayor a 0'}), 400

    bankroll = Bankroll.query.first()
    bankroll.monto_actual += monto

    movimiento = MovimientoBankroll(
        apuesta_id=None,
        monto_cambio=monto,
        saldo_resultante=bankroll.monto_actual,
        descripcion='Depósito manual'
    )
    db.session.add(movimiento)
    db.session.commit()

    return jsonify({'mensaje': 'Depósito registrado', 'bankroll_actual': bankroll.monto_actual})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Crear el bankroll inicial si no existe
        if not Bankroll.query.first():
            db.session.add(Bankroll(monto_actual=0.0))
            db.session.commit()
    app.run(debug=True)