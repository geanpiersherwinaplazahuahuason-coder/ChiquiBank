from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import hashlib
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'chiquibank_secret_key_2024'

class ChiquiBank:
    def __init__(self):
        self.solicitudes_pendientes = []
        self.transacciones = []
        self.saldo_banco = 10000000
        
        self.usuarios = {
            'admin': {
                'password': self._hash_password('admin123'), 
                'tipo': 'admin',
                'nombre': 'Administrador Principal',
                'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generar_numero_cuenta(self):
        while True:
            numero = 'CHQ' + ''.join([str(random.randint(0, 9)) for _ in range(7)])
            if not any(usuario_data.get('numero_cuenta') == numero 
                      for usuario_data in self.usuarios.values()):
                return numero

chiquibank = ChiquiBank()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        if usuario in chiquibank.usuarios:
            if chiquibank.usuarios[usuario]['password'] == chiquibank._hash_password(password):
                session['usuario'] = usuario
                session['tipo'] = chiquibank.usuarios[usuario]['tipo']
                session['nombre'] = chiquibank.usuarios[usuario].get('nombre', '')
                
                if chiquibank.usuarios[usuario]['tipo'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('usuario_dashboard'))
        
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        nombre = request.form['nombre']
        email = request.form['email']
        
        if usuario in chiquibank.usuarios:
            return render_template('registro.html', error='El usuario ya existe')
        
        if len(usuario) < 4:
            return render_template('registro.html', error='Usuario muy corto (mínimo 4 caracteres)')
        
        if len(password) < 6:
            return render_template('registro.html', error='Contraseña muy corta (mínimo 6 caracteres)')
        
        numero_cuenta = chiquibank._generar_numero_cuenta()
        saldo_inicial = 100
        
        chiquibank.usuarios[usuario] = {
            'password': chiquibank._hash_password(password),
            'tipo': 'usuario',
            'nombre': nombre,
            'email': email,
            'numero_cuenta': numero_cuenta,
            'saldo': saldo_inicial,
            'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        chiquibank.transacciones.append({
            'usuario': usuario,
            'tipo': 'apertura_cuenta',
            'monto': saldo_inicial,
            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'estado': 'completado',
            'descripcion': 'Apertura de cuenta + Bono de bienvenida'
        })
        
        chiquibank.transacciones.append({
            'usuario': usuario,
            'tipo': 'deposito',
            'monto': saldo_inicial,
            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'estado': 'completado',
            'descripcion': 'Bono de bienvenida ChiquiBank'
        })
        
        chiquibank.saldo_banco -= saldo_inicial
        
        return render_template('registro_exitoso.html', 
                             usuario=usuario, 
                             numero_cuenta=numero_cuenta,
                             nombre=nombre,
                             saldo_inicial=saldo_inicial)
    
    return render_template('registro.html')

@app.route('/admin')
def admin_dashboard():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))
    
    total_usuarios = len([u for u in chiquibank.usuarios.values() if u['tipo'] == 'usuario'])
    total_solicitudes = len(chiquibank.solicitudes_pendientes)
    
    return render_template('admin.html', 
                         usuario=session['usuario'],
                         nombre=session['nombre'],
                         total_usuarios=total_usuarios,
                         total_solicitudes=total_solicitudes,
                         saldo_banco=chiquibank.saldo_banco)

@app.route('/usuario')
def usuario_dashboard():
    if 'usuario' not in session or session['tipo'] != 'usuario':
        return redirect(url_for('login'))
    
    saldo = chiquibank.usuarios[session['usuario']].get('saldo', 0)
    info_usuario = chiquibank.usuarios[session['usuario']]
    
    return render_template('usuario.html', 
                         usuario=session['usuario'],
                         nombre=session['nombre'],
                         saldo=saldo,
                         info_usuario=info_usuario)

@app.route('/api/solicitudes', methods=['GET'])
def obtener_solicitudes():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 401
    
    return jsonify({'solicitudes': chiquibank.solicitudes_pendientes})

@app.route('/api/procesar_solicitud', methods=['POST'])
def procesar_solicitud():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    solicitud_id = data.get('solicitud_id')
    accion = data.get('accion')
    
    for solicitud in chiquibank.solicitudes_pendientes:
        if solicitud['id'] == solicitud_id:
            usuario = solicitud['usuario']
            tipo = solicitud['tipo']
            monto = solicitud['monto']
            descripcion = solicitud.get('descripcion', '')
            
            if accion == 'aprobar':
                if tipo == 'deposito':
                    chiquibank.usuarios[usuario]['saldo'] += monto
                    chiquibank.saldo_banco += monto
                    estado_final = 'aprobado'
                    mensaje = f'Depósito de {monto} ChiqDollars aprobado'
                elif tipo == 'retiro':
                    chiquibank.usuarios[usuario]['saldo'] -= monto
                    chiquibank.saldo_banco -= monto
                    estado_final = 'aprobado'
                    mensaje = f'Retiro de {monto} ChiqDollars aprobado'
            else:
                estado_final = 'rechazado'
                mensaje = f'Solicitud de {tipo} rechazada'
            
            for trans in chiquibank.transacciones:
                if (trans['usuario'] == usuario and 
                    trans['monto'] == monto and 
                    trans['tipo'] == tipo and
                    trans.get('descripcion') == descripcion and
                    trans['estado'] == 'pendiente_aprobacion'):
                    trans['estado'] = estado_final
                    trans['fecha_procesamiento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trans['procesado_por'] = session['usuario']
                    break
            
            chiquibank.solicitudes_pendientes.remove(solicitud)
            return jsonify({'mensaje': mensaje})
    
    return jsonify({'error': 'Solicitud no encontrada'}), 404

@app.route('/api/solicitar_transaccion', methods=['POST'])
def solicitar_transaccion():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    tipo = data.get('tipo')
    monto = data.get('monto')
    descripcion = data.get('descripcion', '')
    
    usuario = session['usuario']
    
    if tipo == 'retiro' and chiquibank.usuarios[usuario]['saldo'] < monto:
        return jsonify({'error': 'Fondos insuficientes'}), 400
    
    solicitud_id = len(chiquibank.solicitudes_pendientes) + 1
    solicitud = {
        'id': solicitud_id,
        'usuario': usuario,
        'tipo': tipo,
        'monto': monto,
        'descripcion': descripcion,
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'estado': 'pendiente'
    }
    
    chiquibank.solicitudes_pendientes.append(solicitud)
    
    chiquibank.transacciones.append({
        'usuario': usuario,
        'tipo': tipo,
        'monto': monto,
        'descripcion': descripcion,
        'fecha': solicitud['fecha'],
        'estado': 'pendiente_aprobacion'
    })
    
    return jsonify({
        'mensaje': f'Solicitud de {tipo} por {monto} ChiqDollars registrada', 
        'id': solicitud_id
    })

@app.route('/api/transacciones')
def obtener_transacciones():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    usuario = session['usuario']
    transacciones_usuario = [
        trans for trans in chiquibank.transacciones 
        if trans['usuario'] == usuario
    ]
    transacciones_usuario.sort(key=lambda x: x['fecha'], reverse=True)
    
    return jsonify({'transacciones': transacciones_usuario})

@app.route('/api/saldo')
def obtener_saldo():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    usuario = session['usuario']
    saldo = chiquibank.usuarios[usuario].get('saldo', 0)
    return jsonify({'saldo': saldo})

@app.route('/api/info_usuario')
def obtener_info_usuario():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    usuario = session['usuario']
    info = chiquibank.usuarios[usuario].copy()
    info.pop('password', None)
    return jsonify({'info': info})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    print("🏦 ChiquiBank iniciado!")
    print("💳 Moneda: ChiqDollars")
    print("🌐 Servidor web en http://localhost:5000")
    print("👤 Admin: usuario 'admin', contraseña 'admin123'")
    app.run(host='0.0.0.0', port=5000, debug=True)