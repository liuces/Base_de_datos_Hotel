from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
import hashlib
from datetime import datetime
from collections import defaultdict
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from flask import send_file
import io


app = Flask(__name__)
app.secret_key = 'hotel_pacific_reef_2026'

# ============================================================
# CONEXIÓN A LA BASE DE DATOS
# ============================================================
def get_db():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='root1234',
        database='BDD_HOTEL',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================================
# RUTAS PRINCIPALES
# ============================================================

@app.route('/')
def index():
    return redirect(url_for('login'))

# ============================================================
# LOGIN
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo   = request.form['correo']
        password = request.form['password']
        password_hash = hash_password(password)

        print(f"Correo: {correo}")
        print(f"Hash: {password_hash}")

        try:
            db = get_db()
            cursor = db.cursor()
            
            cursor.execute("SELECT * FROM USUARIO WHERE correo_usuario = %s", (correo,))
            usuario_debug = cursor.fetchone()
            print(f"Usuario encontrado: {usuario_debug}")
            
            if usuario_debug:
                print(f"Hash en BD: {usuario_debug['password_hash']}")
                print(f"Coincide: {usuario_debug['password_hash'] == password_hash}")

            cursor.execute("""
                SELECT id_usuario, nombre_usuario, ap_pat_usuario, rol
                FROM USUARIO
                WHERE correo_usuario = %s AND password_hash = %s AND estado = 'activo'
            """, (correo, password_hash))
            usuario = cursor.fetchone()
            print(f"Usuario autenticado: {usuario}")
            db.close()

            if usuario:
                session['id_usuario'] = usuario['id_usuario']
                session['nombre']     = usuario['nombre_usuario'] + ' ' + usuario['ap_pat_usuario']
                session['rol']        = usuario['rol']

                if usuario['rol'] in ['administrador', 'empleado']:
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('disponibilidad'))
            else:
                flash('Correo o contraseña incorrectos.', 'error')

        except Exception as e:
            print(f"ERROR: {str(e)}")
            flash(f'Error: {str(e)}', 'error')

    return render_template('login.html')

# ============================================================
# REGISTRO
# ============================================================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre   = request.form['nombre']
        ap_pat   = request.form['ap_pat']
        ap_mat   = request.form['ap_mat']
        rut      = request.form['rut']
        correo   = request.form['correo']
        telefono = request.form['telefono']
        password = request.form['password']
        password_hash = hash_password(password)

        try:
            db = get_db()
            cursor = db.cursor()

            # Insertar en USUARIO
            cursor.execute("""
                INSERT INTO USUARIO (rut_usuario, nombre_usuario, ap_pat_usuario, ap_mat_usuario,
                correo_usuario, fono_usuario, password_hash, rol)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'cliente')
            """, (rut, nombre, ap_pat, ap_mat, correo, telefono, password_hash))

            id_usuario = cursor.lastrowid

            # Insertar en CLIENTE
            cursor.execute("INSERT INTO CLIENTE (id_usuario) VALUES (%s)", (id_usuario,))
            db.commit()
            db.close()

            flash('Cuenta creada exitosamente. Inicia sesión.', 'success')
            return redirect(url_for('login'))

        except pymysql.err.IntegrityError:
            flash('El correo o RUT ya están registrados.', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')

    return render_template('registro.html')

# ============================================================
# DISPONIBILIDAD
# ============================================================
@app.route('/disponibilidad')
def disponibilidad():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    fecha_entrada = request.args.get('entrada', '')
    fecha_salida  = request.args.get('salida', '')
    personas      = request.args.get('personas', 2)

    habitaciones = []
    try:
        db = get_db()
        cursor = db.cursor()

        if fecha_entrada and fecha_salida:
            # Buscar habitaciones disponibles para las fechas
            cursor.execute("""
                SELECT h.* FROM HABITACION h
                WHERE h.estado_habitacion = 'disponible'
                AND h.capacidad_habitacion >= %s
                AND h.id_habitacion NOT IN (
                    SELECT r.id_habitacion FROM RESERVA r
                    WHERE r.estado_reserva IN ('confirmada','pendiente')
                    AND NOT (r.fecha_salida <= %s OR r.fecha_entrada >= %s)
                )
                ORDER BY h.precio_habitacion
            """, (personas, fecha_entrada, fecha_salida))
        else:
            cursor.execute("""
                SELECT * FROM HABITACION
                ORDER BY precio_habitacion
            """)

        habitaciones = cursor.fetchall()
        db.close()
    except Exception as e:
        flash(f'Error al cargar habitaciones: {str(e)}', 'error')

    return render_template('disponibilidad.html',
                           habitaciones=habitaciones,
                           fecha_entrada=fecha_entrada,
                           fecha_salida=fecha_salida,
                           personas=personas,
                           nombre=session.get('nombre',''))

# ============================================================
# RESERVA Y PAGO
# ============================================================
@app.route('/reserva')
def reserva():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_habitacion = request.args.get('hab')
    fecha_entrada = request.args.get('entrada', '')
    fecha_salida  = request.args.get('salida', '')

    habitacion = None
    noches = 0
    total = 0
    total_30 = 0

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM HABITACION WHERE id_habitacion = %s", (id_habitacion,))
        habitacion = cursor.fetchone()
        db.close()

        if habitacion and fecha_entrada and fecha_salida:
            from datetime import date
            entrada = datetime.strptime(fecha_entrada, '%Y-%m-%d').date()
            salida  = datetime.strptime(fecha_salida, '%Y-%m-%d').date()
            noches  = (salida - entrada).days
            total   = noches * float(habitacion['precio_habitacion'])
            total_30 = total * 0.30

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return render_template('reserva.html',
                           habitacion=habitacion,
                           fecha_entrada=fecha_entrada,
                           fecha_salida=fecha_salida,
                           noches=noches,
                           total=total,
                           total_30=total_30)
@app.route('/detalle')
def detalle():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_habitacion = request.args.get('hab')
    fecha_entrada = request.args.get('entrada', '')
    fecha_salida  = request.args.get('salida', '')

    habitacion = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM HABITACION WHERE id_habitacion = %s", (id_habitacion,))
        habitacion = cursor.fetchone()
        db.close()
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return render_template('detalle.html',
                           habitacion=habitacion,
                           fecha_entrada=fecha_entrada,
                           fecha_salida=fecha_salida)
# ============================================================
# CONFIRMAR RESERVA
# ============================================================
@app.route('/confirmar-reserva', methods=['POST'])
def confirmar_reserva():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    id_habitacion = request.form.get('id_habitacion')
    fecha_entrada = request.form.get('fecha_entrada')
    fecha_salida  = request.form.get('fecha_salida')
    metodo_pago   = request.form.get('metodo_pago', 'tarjeta_credito')
    personas      = request.form.get('personas', 2)

    try:
        db = get_db()
        cursor = db.cursor()

        # Obtener id_cliente
        cursor.execute("""
            SELECT c.id_cliente FROM CLIENTE c
            WHERE c.id_usuario = %s
        """, (session['id_usuario'],))
        cliente = cursor.fetchone()

        # Obtener precio habitación
        cursor.execute("SELECT precio_habitacion FROM HABITACION WHERE id_habitacion = %s", (id_habitacion,))
        hab = cursor.fetchone()

        entrada = datetime.strptime(fecha_entrada, '%Y-%m-%d')
        salida  = datetime.strptime(fecha_salida, '%Y-%m-%d')
        noches  = (salida - entrada).days
        total   = noches * float(hab['precio_habitacion'])
        total_30 = round(total * 0.30, 2)

        # Crear reserva
        cursor.execute("""
            INSERT INTO RESERVA (fecha_entrada, fecha_salida, cantidad_personas,
            monto_total, estado_reserva, id_cliente, id_habitacion)
            VALUES (%s, %s, %s, %s, 'confirmada', %s, %s)
        """, (fecha_entrada, fecha_salida, personas, total, cliente['id_cliente'], id_habitacion))

        id_reserva = cursor.lastrowid

        # Registrar pago
        cursor.execute("""
            INSERT INTO PAGO (id_reserva, monto_pagado, porcentaje_pago, metodo_pago, estado_pago)
            VALUES (%s, %s, 30, %s, 'procesado')
        """, (id_reserva, total_30, metodo_pago))

        # Generar ticket QR
        codigo_qr = f"QR-RES{id_reserva:05d}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        cursor.execute("""
            INSERT INTO TICKET (id_reserva, codigo_qr, estado_ticket)
            VALUES (%s, %s, 'activo')
        """, (id_reserva, codigo_qr))

        # Actualizar estado habitación
        cursor.execute("""
            UPDATE HABITACION SET estado_habitacion = 'ocupada'
            WHERE id_habitacion = %s
        """, (id_habitacion,))

        db.commit()
        db.close()

        return redirect(url_for('ticket', id_reserva=id_reserva))

    except Exception as e:
        flash(f'Error al confirmar reserva: {str(e)}', 'error')
        return redirect(url_for('disponibilidad'))
        

# ============================================================
# TICKET QR
# ============================================================
@app.route('/ticket/<int:id_reserva>')
def ticket(id_reserva):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    datos = None
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT r.id_reserva, 
                   r.fecha_entrada, 
                   r.fecha_salida,
                   r.cantidad_personas,
                   r.monto_total,
                   r.estado_reserva,
                   h.numero_habitacion, 
                   h.tipo_habitacion,
                   h.precio_habitacion,
                   u.nombre_usuario, 
                   u.ap_pat_usuario, 
                   u.correo_usuario,
                   t.codigo_qr, 
                   p.monto_pagado,
                   p.porcentaje_pago,
                   DATEDIFF(r.fecha_salida, r.fecha_entrada) AS noches,
                   (r.monto_total - p.monto_pagado) AS monto_pendiente
            FROM RESERVA r
            JOIN HABITACION h ON r.id_habitacion = h.id_habitacion
            JOIN CLIENTE c ON r.id_cliente = c.id_cliente
            JOIN USUARIO u ON c.id_usuario = u.id_usuario
            JOIN TICKET t ON t.id_reserva = r.id_reserva
            JOIN PAGO p ON p.id_reserva = r.id_reserva
            WHERE r.id_reserva = %s
        """, (id_reserva,))
        datos = cursor.fetchone()
        db.close()
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return render_template('ticket.html', datos=datos)

# ============================================================
# DESCARGAR TICKET EN PDF
# ============================================================
@app.route('/ticket/pdf/<int:id_reserva>')
def ticket_pdf(id_reserva):
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT r.id_reserva, 
                   r.fecha_entrada, 
                   r.fecha_salida,
                   r.cantidad_personas,
                   r.monto_total,
                   r.estado_reserva,
                   h.numero_habitacion, 
                   h.tipo_habitacion,
                   h.precio_habitacion,
                   u.nombre_usuario, 
                   u.ap_pat_usuario, 
                   u.correo_usuario,
                   t.codigo_qr, 
                   p.monto_pagado,
                   DATEDIFF(r.fecha_salida, r.fecha_entrada) AS noches,
                   (r.monto_total - p.monto_pagado) AS monto_pendiente
            FROM RESERVA r
            JOIN HABITACION h ON r.id_habitacion = h.id_habitacion
            JOIN CLIENTE c ON r.id_cliente = c.id_cliente
            JOIN USUARIO u ON c.id_usuario = u.id_usuario
            JOIN TICKET t ON t.id_reserva = r.id_reserva
            JOIN PAGO p ON p.id_reserva = r.id_reserva
            WHERE r.id_reserva = %s
        """, (id_reserva,))
        datos = cursor.fetchone()
        db.close()

        if not datos:
            flash('Reserva no encontrada.', 'error')
            return redirect(url_for('disponibilidad'))

        # Crear PDF en memoria
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import Paragraph, Spacer
        from reportlab.lib.units import cm

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            'Titulo', parent=styles['Heading1'],
            fontSize=20, textColor=colors.HexColor('#1e3a8a'),
            alignment=1, spaceAfter=10
        )
        subtitulo_style = ParagraphStyle(
            'Subtitulo', parent=styles['Normal'],
            fontSize=12, textColor=colors.HexColor('#6b7280'),
            alignment=1, spaceAfter=20
        )
        seccion_style = ParagraphStyle(
            'Seccion', parent=styles['Heading2'],
            fontSize=14, textColor=colors.HexColor('#1f2937'),
            spaceBefore=15, spaceAfter=10
        )

        elementos = []

        # Encabezado
        elementos.append(Paragraph("🌊 Hotel Pacific Reef", titulo_style))
        elementos.append(Paragraph("Confirmación de Reserva", subtitulo_style))

        # Estado
        estado_data = [[f"✓ RESERVA CONFIRMADA — RES-{datos['id_reserva']:05d}"]]
        estado_table = Table(estado_data, colWidths=[16*cm])
        estado_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#d1fae5')),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#065f46')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ]))
        elementos.append(estado_table)
        elementos.append(Spacer(1, 20))

        # Código QR
        elementos.append(Paragraph("Código de acceso", seccion_style))
        qr_data = [[datos['codigo_qr']]]
        qr_table = Table(qr_data, colWidths=[16*cm])
        qr_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f3f4f6')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,-1), 'Courier-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('TOPPADDING', (0,0), (-1,-1), 15),
            ('BOTTOMPADDING', (0,0), (-1,-1), 15),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#9ca3af')),
        ]))
        elementos.append(qr_table)
        elementos.append(Spacer(1, 20))

        # Detalles
        elementos.append(Paragraph("Detalle de la reserva", seccion_style))
        detalles_data = [
            ['Cliente:', f"{datos['nombre_usuario']} {datos['ap_pat_usuario']}"],
            ['Correo:', datos['correo_usuario']],
            ['Habitación:', f"{datos['tipo_habitacion']} N° {datos['numero_habitacion']}"],
            ['Check-in:', str(datos['fecha_entrada'])],
            ['Check-out:', str(datos['fecha_salida'])],
            ['Noches:', str(datos['noches'])],
            ['Personas:', str(datos['cantidad_personas'])],
            ['Valor por noche:', f"${datos['precio_habitacion']:,.0f}"],
        ]
        detalles_table = Table(detalles_data, colWidths=[5*cm, 11*cm])
        detalles_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#6b7280')),
            ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#1f2937')),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
        ]))
        elementos.append(detalles_table)
        elementos.append(Spacer(1, 20))

        # Pagos
        elementos.append(Paragraph("Resumen de pago", seccion_style))
        pagos_data = [
            ['Total estadía', f"${datos['monto_total']:,.0f}"],
            ['✓ Pagado ahora (30%)', f"${datos['monto_pagado']:,.0f}"],
            ['⏳ Pendiente al llegar (70%)', f"${datos['monto_pendiente']:,.0f}"],
        ]
        pagos_table = Table(pagos_data, colWidths=[10*cm, 6*cm])
        pagos_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 11),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
            ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#d1fae5')),
            ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#fef3c7')),
            ('TEXTCOLOR', (0,1), (-1,1), colors.HexColor('#065f46')),
            ('TEXTCOLOR', (0,2), (-1,2), colors.HexColor('#92400e')),
            ('TOPPADDING', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        elementos.append(pagos_table)
        elementos.append(Spacer(1, 30))

        # Pie
        pie_style = ParagraphStyle(
            'Pie', parent=styles['Normal'],
            fontSize=9, textColor=colors.HexColor('#6b7280'),
            alignment=1
        )
        elementos.append(Paragraph(
            "Presenta este ticket al momento del check-in.<br/>"
            "Hotel Pacific Reef — Viña del Mar, Chile",
            pie_style
        ))

        doc.build(elementos)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'ticket_reserva_{id_reserva:05d}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        flash(f'Error al generar PDF: {str(e)}', 'error')
        return redirect(url_for('ticket', id_reserva=id_reserva))

# ============================================================
# PANEL ADMINISTRADOR
# ============================================================
@app.route('/admin')
def admin_dashboard():
    if 'id_usuario' not in session or session.get('rol') not in ['administrador','empleado']:
        return redirect(url_for('login'))

    stats = {}
    reservas_recientes = []

    try:
        db = get_db()
        cursor = db.cursor()

        # ───────────── STATS PRINCIPALES ─────────────
        cursor.execute("SELECT COUNT(*) as total FROM RESERVA WHERE estado_reserva = 'confirmada'")
        stats['reservas_activas'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM RESERVA WHERE fecha_entrada = CURDATE()")
        stats['checkin_hoy'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM RESERVA WHERE fecha_salida = CURDATE()")
        stats['checkout_hoy'] = cursor.fetchone()['total']

        # ───────────── HABITACIONES ─────────────
        cursor.execute("SELECT COUNT(*) as total FROM HABITACION")
        stats['total_habitaciones'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM HABITACION WHERE estado_habitacion = 'ocupada'")
        stats['ocupadas'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM HABITACION WHERE estado_habitacion = 'disponible'")
        stats['disponibles'] = cursor.fetchone()['total']

        cursor.execute("SELECT COUNT(*) as total FROM HABITACION WHERE estado_habitacion = 'mantencion'")
        stats['mantencion'] = cursor.fetchone()['total']

        # ───────────── OCUPACIÓN (CONSISTENTE) ─────────────
        if stats['total_habitaciones'] > 0:
            stats['ocupacion'] = round(
                (stats['ocupadas'] / stats['total_habitaciones']) * 100,
                1
            )
        else:
            stats['ocupacion'] = 0

        # ───────────── RESERVAS RECIENTES ─────────────
        cursor.execute("""
            SELECT r.id_reserva,
                   CONCAT(u.nombre_usuario,' ',u.ap_pat_usuario) as cliente,
                   h.numero_habitacion,
                   r.estado_reserva,
                   r.fecha_entrada,
                   r.monto_total
            FROM RESERVA r
            JOIN CLIENTE c ON r.id_cliente = c.id_cliente
            JOIN USUARIO u ON c.id_usuario = u.id_usuario
            JOIN HABITACION h ON r.id_habitacion = h.id_habitacion
            ORDER BY r.fecha_creacion DESC
            LIMIT 5
        """)
        reservas_recientes = cursor.fetchall()

        db.close()

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    hoy = datetime.now()

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

    fecha_formateada = f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"    

    return render_template(
        'admin_dashboard.html',
        stats=stats,
        reservas=reservas_recientes,
        nombre=session.get('nombre', ''),
        fecha=fecha_formateada
    )

# ============================================================
# ADMIN — GESTIÓN RESERVAS
# ============================================================
@app.route('/admin/reservas')
def admin_reservas():
    if 'id_usuario' not in session or session.get('rol') not in ['administrador','empleado']:
        return redirect(url_for('login'))

    reservas = []

    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT r.id_reserva,
                   CONCAT(u.nombre_usuario,' ',u.ap_pat_usuario) AS cliente,
                   h.numero_habitacion,
                   h.tipo_habitacion,
                   r.fecha_entrada,
                   r.fecha_salida,
                   r.estado_reserva,
                   r.monto_total
            FROM RESERVA r
            JOIN CLIENTE c ON r.id_cliente = c.id_cliente
            JOIN USUARIO u ON c.id_usuario = u.id_usuario
            JOIN HABITACION h ON r.id_habitacion = h.id_habitacion
            ORDER BY r.fecha_entrada DESC
        """)

        reservas = cursor.fetchall()
        db.close()

    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    # ✅ Fecha SIEMPRE definida
    hoy = datetime.now()

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

    fecha_formateada = f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month - 1]} de {hoy.year}"

    return render_template(
        'admin_reservas.html',
        reservas=reservas,
        nombre=session.get('nombre', ''),
        fecha=fecha_formateada
    )

# ============================================================
# ADMIN — GESTIÓN USUARIOS
# ============================================================
@app.route('/admin/usuarios')
def admin_usuarios():
    if 'id_usuario' not in session or session.get('rol') not in ['administrador']:
        return redirect(url_for('login'))

    usuarios = []
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT id_usuario, rut_usuario, nombre_usuario, ap_pat_usuario,
                   correo_usuario, fono_usuario, rol, estado, fecha_registro
            FROM USUARIO ORDER BY fecha_registro DESC
        """)
        usuarios = cursor.fetchall()
        db.close()
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return render_template('admin_usuarios.html', usuarios=usuarios)

@app.route('/admin/usuarios/guardar', methods=['POST'])
def guardar_usuario():
    try:
        nombre = request.form['nombre']
        ap_pat = request.form['ap_pat']
        ap_mat = request.form['ap_mat']
        rut = request.form['rut']
        correo = request.form['correo']
        telefono = request.form.get('telefono', '')
        rol = request.form['rol']
        password = request.form.get('password', '')

        if not password:
            password = "123456"

        password_hash = hash_password(password)

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO USUARIO (
                rut_usuario,
                nombre_usuario,
                ap_pat_usuario,
                ap_mat_usuario,
                correo_usuario,
                fono_usuario,
                password_hash,
                rol
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            rut,
            nombre,
            ap_pat,
            ap_mat,
            correo,
            telefono,
            password_hash,
            rol
        ))

        db.commit()
        db.close()

        print("✔ USUARIO CREADO OK")

        return redirect(url_for('admin_usuarios'))

    except Exception as e:
        print("❌ ERROR:", str(e))
        return f"ERROR: {str(e)}"

# ============================================================
# ADMIN — REPORTES
# ============================================================
@app.route('/admin/reportes')
def admin_reportes():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    desde = request.args.get('desde')
    hasta = request.args.get('hasta')
    tipo = request.args.get('tipo')

    query = """
        SELECT r.id_reserva,
               CONCAT(u.nombre_usuario,' ',u.ap_pat_usuario),
               h.numero_habitacion,
               h.tipo_habitacion,
               r.fecha_entrada,
               r.fecha_salida,
               r.estado_reserva,
               r.monto_total
        FROM RESERVA r
        JOIN CLIENTE c ON r.id_cliente = c.id_cliente
        JOIN USUARIO u ON c.id_usuario = u.id_usuario
        JOIN HABITACION h ON r.id_habitacion = h.id_habitacion
        WHERE 1=1
    """

    params = []

    if desde:
        query += " AND r.fecha_entrada >= %s"
        params.append(desde)

    if hasta:
        query += " AND r.fecha_salida <= %s"
        params.append(hasta)

    if tipo:
        query += " AND h.tipo_habitacion = %s"
        params.append(tipo)

    query += " ORDER BY r.fecha_entrada DESC"

    db = get_db()
    cursor = db.cursor()
    cursor.execute(query, params)
    reservas = cursor.fetchall()
    db.close()

    total_reservas = len(reservas)
    total_ingresos = sum(float(r['monto_total']) for r in reservas) if reservas else 0

    reservas_por_tipo = defaultdict(int)
    ingresos_por_tipo = defaultdict(int)

    for r in reservas:
        tipo = r['tipo_habitacion']
        reservas_por_tipo[tipo] += 1
        ingresos_por_tipo[tipo] += float(r['monto_total'])

    # OCUPACIÓN
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM HABITACION")
    total_habitaciones = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM HABITACION WHERE estado_habitacion = 'ocupada'")
    ocupadas = cursor.fetchone()['total']

    ocupacion = (ocupadas / total_habitaciones * 100) if total_habitaciones else 0

    db.close() 

    return render_template(
        'admin_reportes.html',
        reservas=reservas,
        total_reservas=len(reservas),
        total_ingresos=total_ingresos,
        reservas_por_tipo=reservas_por_tipo,
        ingresos_por_tipo=ingresos_por_tipo,
        ocupacion=round(ocupacion, 1)
    )

@app.route('/admin/reservas/pdf')
def exportar_reservas_pdf():
    if 'id_usuario' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT r.id_reserva,
               CONCAT(u.nombre_usuario,' ',u.ap_pat_usuario) AS cliente,
               h.numero_habitacion,
               h.tipo_habitacion,
               r.fecha_entrada,
               r.fecha_salida,
               r.estado_reserva,
               r.monto_total
        FROM RESERVA r
        JOIN CLIENTE c ON r.id_cliente = c.id_cliente
        JOIN USUARIO u ON c.id_usuario = u.id_usuario
        JOIN HABITACION h ON r.id_habitacion = h.id_habitacion
        ORDER BY r.fecha_entrada DESC
    """)

    reservas = cursor.fetchall()
    db.close()

    # Crear PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    data = []
    
    # Encabezados
    data.append([
        "ID", "Cliente", "Habitación", "Tipo",
        "Entrada", "Salida", "Estado", "Monto"
    ])

    # Datos
    for r in reservas:
        data.append([
            r['id_reserva'],
            r['cliente'],
            r['numero_habitacion'],
            r['tipo_habitacion'],
            str(r['fecha_entrada']),
            str(r['fecha_salida']),
            r['estado_reserva'],
            f"${r['monto_total']}"
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))

    doc.build([table])
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name='reporte_reservas.pdf',
        mimetype='application/pdf'
    )
# ============================================================
# LOGOUT
# ============================================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ============================================================
# INICIAR SERVIDOR
# ============================================================
if __name__ == '__main__':
    app.run(debug=True)
