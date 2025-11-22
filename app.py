from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import json
import hashlib
import random
from datetime import datetime, timedelta
import os
import math

app = Flask(__name__)
app.secret_key = 'chiquibank_secreto_realista_2024'

class BancoRealista:
    def __init__(self):
        self.solicitudes_pendientes = []
        self.transacciones = []
        self.saldo_banco = 50000000  # 50 millones de capital inicial
        self.tasa_interes_activa = 0.12  # 12% anual para préstamos
        self.tasa_interes_pasiva = 0.03  # 3% anual para ahorros
        self.impuesto_transacciones = 0.02  # 2% de impuesto
        
        # Mercado de valores simulado
        self.acciones = {
            'TECH': {'precio': 150, 'volatilidad': 0.15, 'dividendo': 0.04},
            'ENERGY': {'precio': 80, 'volatilidad': 0.08, 'dividendo': 0.06},
            'BANK': {'precio': 120, 'volatilidad': 0.12, 'dividendo': 0.05},
            'REALESTATE': {'precio': 95, 'volatilidad': 0.10, 'dividendo': 0.03}
        }
        
        # Eventos deportivos para apuestas
        self.eventos_deportivos = [
            {'id': 1, 'evento': 'Barcelona vs Real Madrid', 'cuota_local': 2.1, 'cuota_visitante': 3.2, 'cuota_empate': 3.0},
            {'id': 2, 'evento': 'Messi vs Ronaldo - Partido Amistoso', 'cuota_local': 1.8, 'cuota_visitante': 4.0, 'cuota_empate': 3.5},
            {'id': 3, 'evento': 'Champions League Final', 'cuota_local': 2.5, 'cuota_visitante': 2.7, 'cuota_empate': 3.1}
        ]
        
        # Usuarios iniciales
        self.usuarios = {
            'admin': {
                'password': self._hash_password('admin123'), 
                'tipo': 'admin',
                'nombre': 'Director del Banco',
                'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'saldo': 0
            }
        }
        
        # Portafolios de inversión
        self.portafolios = {}
    
    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generar_numero_cuenta(self):
        while True:
            numero = 'CHQ' + ''.join([str(random.randint(0, 9)) for _ in range(7)])
            if not any(usuario_data.get('numero_cuenta') == numero 
                      for usuario_data in self.usuarios.values()):
                return numero
    
    def calcular_impuesto(self, monto):
        return monto * self.impuesto_transacciones
    
    def actualizar_mercado(self):
        """Actualiza los precios del mercado de valores"""
        for simbolo, datos in self.acciones.items():
            cambio = random.gauss(0, datos['volatilidad'])
            nuevo_precio = datos['precio'] * (1 + cambio)
            self.acciones[simbolo]['precio'] = max(10, nuevo_precio)  # Mínimo 10 ChiqDollars

banco = BancoRealista()

# Actualizar mercado cada vez que se accede
@app.before_request
def actualizar_mercado_antes():
    if random.random() < 0.3:  # 30% de probabilidad de actualizar
        banco.actualizar_mercado()

# ======================
# RUTAS PRINCIPALES
# ======================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        if usuario in banco.usuarios:
            if banco.usuarios[usuario]['password'] == banco._hash_password(password):
                session['usuario'] = usuario
                session['tipo'] = banco.usuarios[usuario]['tipo']
                session['nombre'] = banco.usuarios[usuario].get('nombre', '')
                
                if banco.usuarios[usuario]['tipo'] == 'admin':
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
        
        if usuario in banco.usuarios:
            return render_template('registro.html', error='El usuario ya existe')
        
        if len(usuario) < 4:
            return render_template('registro.html', error='Usuario muy corto (mínimo 4 caracteres)')
        
        if len(password) < 6:
            return render_template('registro.html', error='Contraseña muy corta (mínimo 6 caracteres)')
        
        numero_cuenta = banco._generar_numero_cuenta()
        saldo_inicial = 1000  # Más realista: 1000 en lugar de 100
        
        banco.usuarios[usuario] = {
            'password': banco._hash_password(password),
            'tipo': 'usuario',
            'nombre': nombre,
            'email': email,
            'numero_cuenta': numero_cuenta,
            'saldo': saldo_inicial,
            'fecha_creacion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'inversiones': {},
            'prestamos': []
        }
        
        # Inicializar portafolio
        banco.portafolios[usuario] = {}
        
        banco.transacciones.append({
            'usuario': usuario,
            'tipo': 'apertura_cuenta',
            'monto': saldo_inicial,
            'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'estado': 'completado',
            'descripcion': 'Apertura de cuenta + Capital inicial'
        })
        
        return render_template('registro_exitoso.html', 
                             usuario=usuario, 
                             numero_cuenta=numero_cuenta,
                             nombre=nombre,
                             saldo_inicial=saldo_inicial)
    
    return render_template('registro.html')

# ======================
# PANEL DE USUARIO MEJORADO
# ======================

@app.route('/usuario')
def usuario_dashboard():
    if 'usuario' not in session or session['tipo'] != 'usuario':
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    info_usuario = banco.usuarios[usuario]
    saldo = info_usuario.get('saldo', 0)
    
    # Calcular valor del portafolio
    valor_portafolio = 0
    if usuario in banco.portafolios:
        for simbolo, cantidad in banco.portafolios[usuario].items():
            if simbolo in banco.acciones:
                valor_portafolio += cantidad * banco.acciones[simbolo]['precio']
    
    # Calcular deuda total
    deuda_total = sum([p['monto_restante'] for p in info_usuario.get('prestamos', [])])
    
    patrimonio = saldo + valor_portafolio - deuda_total
    
    return render_template('usuario_realista.html', 
                         usuario=usuario,
                         nombre=session['nombre'],
                         saldo=saldo,
                         info_usuario=info_usuario,
                         valor_portafolio=valor_portafolio,
                         deuda_total=deuda_total,
                         patrimonio=patrimonio)

# ======================
# SISTEMA DE INVERSIONES REALISTA
# ======================

@app.route('/inversiones')
def inversiones():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    portafolio = banco.portafolios.get(usuario, {})
    
    # Calcular ganancias/perdidas
    ganancias_portafolio = {}
    for simbolo, cantidad in portafolio.items():
        if simbolo in banco.acciones:
            precio_actual = banco.acciones[simbolo]['precio']
            # En un sistema real, aquí calcularías el precio de compra
            ganancias_portafolio[simbolo] = cantidad * precio_actual
    
    return render_template('inversiones.html',
                         acciones=banco.acciones,
                         portafolio=portafolio,
                         ganancias_portafolio=ganancias_portafolio,
                         usuario=usuario)

@app.route('/comprar_acciones', methods=['POST'])
def comprar_acciones():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    simbolo = data.get('simbolo')
    cantidad = int(data.get('cantidad', 0))
    usuario = session['usuario']
    
    if simbolo not in banco.acciones:
        return jsonify({'error': 'Acción no encontrada'}), 404
    
    precio = banco.acciones[simbolo]['precio']
    costo_total = precio * cantidad
    comision = costo_total * 0.01  # 1% de comisión
    
    total_a_pagar = costo_total + comision
    
    if banco.usuarios[usuario]['saldo'] < total_a_pagar:
        return jsonify({'error': 'Fondos insuficientes'}), 400
    
    # Ejecutar compra
    banco.usuarios[usuario]['saldo'] -= total_a_pagar
    
    # Actualizar portafolio
    if usuario not in banco.portafolios:
        banco.portafolios[usuario] = {}
    
    if simbolo in banco.portafolios[usuario]:
        banco.portafolios[usuario][simbolo] += cantidad
    else:
        banco.portafolios[usuario][simbolo] = cantidad
    
    # Registrar transacción
    banco.transacciones.append({
        'usuario': usuario,
        'tipo': 'compra_acciones',
        'monto': total_a_pagar,
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'estado': 'completado',
        'descripcion': f'Compra de {cantidad} acciones {simbolo} a {precio:.2f} c/u'
    })
    
    return jsonify({
        'mensaje': f'Compra exitosa: {cantidad} acciones {simbolo}',
        'costo_total': costo_total,
        'comision': comision,
        'nuevo_saldo': banco.usuarios[usuario]['saldo']
    })

# ======================
# APUESTAS DEPORTIVAS REALISTAS
# ======================

@app.route('/apuestas_deportivas')
def apuestas_deportivas():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    return render_template('apuestas_deportivas.html',
                         eventos=banco.eventos_deportivos,
                         usuario=session['usuario'])

@app.route('/apostar_deportes', methods=['POST'])
def apostar_deportes():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    evento_id = int(data.get('evento_id'))
    monto = float(data.get('monto'))
    resultado = data.get('resultado')  # 'local', 'visitante', 'empate'
    usuario = session['usuario']
    
    # Encontrar evento
    evento = next((e for e in banco.eventos_deportivos if e['id'] == evento_id), None)
    if not evento:
        return jsonify({'error': 'Evento no encontrada'}), 404
    
    if banco.usuarios[usuario]['saldo'] < monto:
        return jsonify({'error': 'Fondos insuficientes'}), 400
    
    # Determinar cuota
    if resultado == 'local':
        cuota = evento['cuota_local']
    elif resultado == 'visitante':
        cuota = evento['cuota_visitante']
    else:
        cuota = evento['cuota_empate']
    
    # Simular resultado (en la realidad sería impredecible)
    resultados_posibles = ['local', 'visitante', 'empate']
    pesos = [0.45, 0.35, 0.2]  # Probabilidades aproximadas
    resultado_real = random.choices(resultados_posibles, weights=pesos)[0]
    
    ganancia = 0
    if resultado == resultado_real:
        ganancia = monto * cuota
        mensaje = f"🎉 ¡GANASTE! Resultado: {resultado_real}"
        banco.usuarios[usuario]['saldo'] += ganancia
        estado = 'ganada'
    else:
        banco.usuarios[usuario]['saldo'] -= monto
        mensaje = f"😞 Perdiste. Resultado real: {resultado_real}"
        estado = 'perdida'
        ganancia = -monto
    
    # Registrar apuesta
    banco.transacciones.append({
        'usuario': usuario,
        'tipo': 'apuesta_deportiva',
        'monto': ganancia,
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'estado': estado,
        'descripcion': f'Apuesta en {evento["evento"]}: {resultado} (Cuota: {cuota}x)'
    })
    
    return jsonify({
        'mensaje': mensaje,
        'resultado_real': resultado_real,
        'ganancia': ganancia,
        'nuevo_saldo': banco.usuarios[usuario]['saldo']
    })

# ======================
# SISTEMA DE PRÉSTAMOS
# ======================

@app.route('/prestamos')
def prestamos():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    usuario = session['usuario']
    prestamos_usuario = banco.usuarios[usuario].get('prestamos', [])
    
    return render_template('prestamos.html',
                         prestamos=prestamos_usuario,
                         tasa_interes=banco.tasa_interes_activa * 100,
                         usuario=usuario)

@app.route('/solicitar_prestamo', methods=['POST'])
def solicitar_prestamo():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    monto = float(data.get('monto'))
    plazo_meses = int(data.get('plazo_meses', 12))
    usuario = session['usuario']
    
    # Análisis de riesgo básico
    salario_promedio = 2000  # Salario promedio simulado
    capacidad_pago = salario_promedio * 0.3  # 30% del salario para deudas
    
    cuota_mensual = (monto * (1 + banco.tasa_interes_activa)) / plazo_meses
    
    if cuota_mensual > capacidad_pago:
        return jsonify({'error': 'Préstamo rechazado: capacidad de pago insuficiente'}), 400
    
    # Crear préstamo
    prestamo = {
        'id': len(banco.usuarios[usuario].get('prestamos', [])) + 1,
        'monto_original': monto,
        'monto_restante': monto * (1 + banco.tasa_interes_activa),
        'tasa_interes': banco.tasa_interes_activa,
        'plazo_meses': plazo_meses,
        'cuota_mensual': cuota_mensual,
        'fecha_otorgamiento': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'estado': 'activo'
    }
    
    if 'prestamos' not in banco.usuarios[usuario]:
        banco.usuarios[usuario]['prestamos'] = []
    
    banco.usuarios[usuario]['prestamos'].append(prestamo)
    banco.usuarios[usuario]['saldo'] += monto
    banco.saldo_banco -= monto
    
    banco.transacciones.append({
        'usuario': usuario,
        'tipo': 'prestamo_otorgado',
        'monto': monto,
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'estado': 'completado',
        'descripcion': f'Préstamo aprobado: {monto} a {plazo_meses} meses'
    })
    
    return jsonify({
        'mensaje': 'Préstamo aprobado',
        'prestamo': prestamo,
        'nuevo_saldo': banco.usuarios[usuario]['saldo']
    })

# ======================
# ADMINISTRACIÓN
# ======================

@app.route('/admin')
def admin_dashboard():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return redirect(url_for('login'))
    
    total_usuarios = len([u for u in banco.usuarios.values() if u['tipo'] == 'usuario'])
    total_solicitudes = len(banco.solicitudes_pendientes)
    
    # Calcular métricas financieras
    total_depositos = sum([u.get('saldo', 0) for u in banco.usuarios.values() if u['tipo'] == 'usuario'])
    total_prestamos = sum([sum(p['monto_restante'] for p in u.get('prestamos', [])) 
                          for u in banco.usuarios.values() if u['tipo'] == 'usuario'])
    
    return render_template('admin.html', 
                         usuario=session['usuario'],
                         nombre=session['nombre'],
                         total_usuarios=total_usuarios,
                         total_solicitudes=total_solicitudes,
                         saldo_banco=banco.saldo_banco,
                         total_depositos=total_depositos,
                         total_prestamos=total_prestamos)

@app.route('/api/solicitudes', methods=['GET'])
def obtener_solicitudes():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 401
    
    return jsonify({'solicitudes': banco.solicitudes_pendientes})

@app.route('/api/procesar_solicitud', methods=['POST'])
def procesar_solicitud():
    if 'usuario' not in session or session['tipo'] != 'admin':
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    solicitud_id = data.get('solicitud_id')
    accion = data.get('accion')
    
    for solicitud in banco.solicitudes_pendientes:
        if solicitud['id'] == solicitud_id:
            usuario = solicitud['usuario']
            tipo = solicitud['tipo']
            monto = solicitud['monto']
            descripcion = solicitud.get('descripcion', '')
            
            if accion == 'aprobar':
                if tipo == 'deposito':
                    # Aplicar impuesto
                    impuesto = banco.calcular_impuesto(monto)
                    monto_neto = monto - impuesto
                    
                    banco.usuarios[usuario]['saldo'] += monto_neto
                    banco.saldo_banco += monto_neto
                    estado_final = 'aprobado'
                    mensaje = f'Depósito de {monto} aprobado (Impuesto: -{impuesto})'
                elif tipo == 'retiro':
                    if banco.usuarios[usuario]['saldo'] >= monto:
                        banco.usuarios[usuario]['saldo'] -= monto
                        banco.saldo_banco -= monto
                        estado_final = 'aprobado'
                        mensaje = f'Retiro de {monto} aprobado'
                    else:
                        estado_final = 'rechazado_fondos'
                        mensaje = 'Fondos insuficientes'
            else:
                estado_final = 'rechazado'
                mensaje = f'Solicitud de {tipo} rechazada'
            
            # Actualizar transacción
            for trans in banco.transacciones:
                if (trans['usuario'] == usuario and 
                    trans['monto'] == monto and 
                    trans['tipo'] == tipo and
                    trans.get('descripcion') == descripcion and
                    trans['estado'] == 'pendiente_aprobacion'):
                    trans['estado'] = estado_final
                    trans['fecha_procesamiento'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    trans['procesado_por'] = session['usuario']
                    break
            
            banco.solicitudes_pendientes.remove(solicitud)
            return jsonify({'mensaje': mensaje})
    
    return jsonify({'error': 'Solicitud no encontrada'}), 404

# ======================
# TRANSACCIONES BÁSICAS
# ======================

@app.route('/api/solicitar_transaccion', methods=['POST'])
def solicitar_transaccion():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    data = request.json
    tipo = data.get('tipo')
    monto = data.get('monto')
    descripcion = data.get('descripcion', '')
    
    usuario = session['usuario']
    
    if tipo == 'retiro' and banco.usuarios[usuario]['saldo'] < monto:
        return jsonify({'error': 'Fondos insuficientes'}), 400
    
    solicitud_id = len(banco.solicitudes_pendientes) + 1
    solicitud = {
        'id': solicitud_id,
        'usuario': usuario,
        'tipo': tipo,
        'monto': monto,
        'descripcion': descripcion,
        'fecha': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'estado': 'pendiente'
    }
    
    banco.solicitudes_pendientes.append(solicitud)
    
    banco.transacciones.append({
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
        trans for trans in banco.transacciones 
        if trans['usuario'] == usuario
    ]
    transacciones_usuario.sort(key=lambda x: x['fecha'], reverse=True)
    
    return jsonify({'transacciones': transacciones_usuario})

@app.route('/api/saldo')
def obtener_saldo():
    if 'usuario' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    usuario = session['usuario']
    saldo = banco.usuarios[usuario].get('saldo', 0)
    return jsonify({'saldo': saldo})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ======================
# INICIO DEL SERVIDOR
# ======================

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print("=" * 70)
    print("🏦 CHIQUIBANK - SISTEMA BANCARIO REALISTA")
    print("💳 Moneda: ChiqDollars")
    print(f"🌐 Servidor ejecutándose en puerto: {port}")
    print("👤 Administrador: usuario 'admin', contraseña 'admin123'")
    print("💰 Capital inicial del banco: 50,000,000 ChiqDollars")
    print("📈 Sistema de inversiones activado")
    print("🎯 Apuestas deportivas disponibles")
    print("🏠 Sistema de préstamos con análisis de riesgo")
    print("=" * 70)
    app.run(host='0.0.0.0', port=port, debug=False)