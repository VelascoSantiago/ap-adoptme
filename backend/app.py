from flask import Flask, jsonify, request
import pymysql
import redis
import time

app = Flask(__name__)

# --- CONEXIÓN A MYSQL ---
def obtener_conexion():
    retries = 5
    while retries > 0:
        try:
            conexion = pymysql.connect(
                host='mysql',
                user='root',
                password='root',
                database='adoptme_db',
                cursorclass=pymysql.cursors.DictCursor
            )
            return conexion
        except pymysql.MySQLError as e:
            retries -= 1
            time.sleep(2)
    raise Exception("No se pudo conectar a la base de datos.")

# --- CONEXIÓN A REDIS ---
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# --- FUNCIÓN AUXILIAR: Formatear Fechas ---
# Convierte los objetos datetime de MySQL a texto para que jsonify no falle
def sanitizar_fechas(registro):
    for key, value in registro.items():
        if hasattr(value, 'isoformat'): # Si es una fecha/hora, la convierte a string
            registro[key] = value.isoformat()
    return registro


@app.route('/')
def index():
    return jsonify({
        "mensaje": "¡Bienvenido a la API de AdoptMe!",
        "estado": "El backend está conectado a MySQL y funcionando."
    })


# ==========================================
# MÓDULO 1: MASCOTAS
# ==========================================

@app.route('/agregar', methods=['POST'])
def agregar_mascota():
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se enviaron datos"}), 400

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """INSERT INTO mascotas 
                     (nombre, especie, raza, fecha_nacimiento_aprox, tamano, salud, estado_adopcion, notas_medicas) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            valores = (
                datos.get('nombre'), datos.get('especie'), datos.get('raza', 'Mestizo'),
                datos.get('fecha_nacimiento_aprox'), datos.get('tamano'), datos.get('salud'),
                datos.get('estado_adopcion', 'disponible'), datos.get('notas_medicas', '')
            )
            cursor.execute(sql, valores)
        conexion.commit()
        return jsonify({"mensaje": "Mascota registrada", "id_asignado": cursor.lastrowid}), 201
    finally:
        conexion.close()

@app.route('/mascotas', methods=['GET'])
def ver_mascotas():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM mascotas")
            mascotas = [sanitizar_fechas(m) for m in cursor.fetchall()]
        return jsonify(mascotas), 200
    finally:
        conexion.close()

@app.route('/mascotas/<int:id_mascota>', methods=['DELETE'])
def eliminar_mascota(id_mascota):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM mascotas WHERE id = %s", (id_mascota,))
        conexion.commit()
        return jsonify({"mensaje": f"Mascota {id_mascota} eliminada del sistema."}), 200
    finally:
        conexion.close()


# ==========================================
# MÓDULO 2: USUARIOS
# ==========================================

@app.route('/usuarios', methods=['POST'])
def registrar_usuario():
    datos = request.get_json()
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """INSERT INTO usuarios (nombre_completo, email, password_hash, telefono, rol) 
                     VALUES (%s, %s, %s, %s, %s)"""
            valores = (
                datos.get('nombre_completo'), datos.get('email'), 
                datos.get('password'), # En producción aquí aplicaríamos un hash de seguridad
                datos.get('telefono'), datos.get('rol', 'adoptante')
            )
            cursor.execute(sql, valores)
        conexion.commit()
        return jsonify({"mensaje": "Usuario registrado", "id_asignado": cursor.lastrowid}), 201
    finally:
        conexion.close()

@app.route('/usuarios', methods=['GET'])
def ver_usuarios():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Omitimos el password_hash por seguridad
            cursor.execute("SELECT id, nombre_completo, email, telefono, rol, activo, creado_en FROM usuarios")
            usuarios = [sanitizar_fechas(u) for u in cursor.fetchall()]
        return jsonify(usuarios), 200
    finally:
        conexion.close()


# ==========================================
# MÓDULO 3: SOLICITUDES (La parte relacional)
# ==========================================

@app.route('/solicitudes', methods=['POST'])
def crear_solicitud():
    datos = request.get_json()
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "INSERT INTO solicitudes (usuario_id, mascota_id) VALUES (%s, %s)"
            cursor.execute(sql, (datos.get('usuario_id'), datos.get('mascota_id')))
        conexion.commit()
        return jsonify({"mensaje": "Solicitud creada, en espera de revisión"}), 201
    except pymysql.err.IntegrityError:
        return jsonify({"error": "El usuario o la mascota no existen"}), 400
    finally:
        conexion.close()

@app.route('/solicitudes', methods=['GET'])
def ver_solicitudes():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # ¡Magia SQL! Unimos las 3 tablas para dar una respuesta legible
            sql = """
                SELECT s.id, u.nombre_completo AS adoptante, u.email, 
                       m.nombre AS mascota, m.especie, s.estado, s.creado_en 
                FROM solicitudes s
                JOIN usuarios u ON s.usuario_id = u.id
                JOIN mascotas m ON s.mascota_id = m.id
            """
            cursor.execute(sql)
            solicitudes = [sanitizar_fechas(s) for s in cursor.fetchall()]
        return jsonify(solicitudes), 200
    finally:
        conexion.close()

@app.route('/solicitudes/<int:id_solicitud>/estado', methods=['PATCH'])
def cambiar_estado_solicitud(id_solicitud):
    datos = request.get_json()
    nuevo_estado = datos.get('estado') # Puede ser 'aprobada', 'rechazada', etc.
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # 1. Actualizamos la solicitud
            cursor.execute("UPDATE solicitudes SET estado = %s WHERE id = %s", (nuevo_estado, id_solicitud))
            
            # 2. Si se aprueba, lanzamos un UPDATE automático a la mascota usando una subconsulta
            if nuevo_estado == 'aprobada':
                sql_mascota = """
                    UPDATE mascotas 
                    SET estado_adopcion = 'adoptado' 
                    WHERE id = (SELECT mascota_id FROM solicitudes WHERE id = %s)
                """
                cursor.execute(sql_mascota, (id_solicitud,))
                
        conexion.commit() # Si ambas operaciones tienen éxito, se guardan en disco
        return jsonify({"mensaje": f"Solicitud {id_solicitud} marcada como {nuevo_estado}"}), 200
    finally:
        conexion.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)