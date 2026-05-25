from flask import Flask, jsonify, request
import pymysql
import redis
import time
import uuid
from functools import wraps

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

# --- DECORADOR: Validar que el usuario inició sesión (Admin o Adoptante) ---
def requiere_login(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Falta el token de acceso. Por favor, inicia sesión."}), 401
        
        # Extraemos el ID del usuario directamente de Redis
        usuario_id = redis_client.get(token)
        if not usuario_id:
            return jsonify({"error": "Sesión expirada o inválida."}), 401
            
        # Pasamos el usuario_id como un argumento invisible a la función de la ruta
        return f(usuario_id, *args, **kwargs)
    return decorador

# --- DECORADOR: Validar permisos estrictos de Administrador ---
def requiere_admin(f):
    @wraps(f)
    def decorador(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "Falta el token de acceso"}), 401
        
        usuario_id = redis_client.get(token)
        if not usuario_id:
            return jsonify({"error": "Sesión inválida o expirada."}), 401
            
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT rol FROM usuarios WHERE id = %s", (usuario_id,))
                usuario = cursor.fetchone()
                if not usuario or usuario['rol'] != 'admin':
                    return jsonify({"error": "Acceso denegado. Se requieren permisos de administrador."}), 403
        finally:
            conexion.close()
            
        return f(*args, **kwargs)
    return decorador

# --- ENDPOINT DE LOGIN ---
@app.route('/login', methods=['POST'])
def login():
    datos = request.get_json()
    email = datos.get('email')
    password = datos.get('password') 
    
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id, rol FROM usuarios WHERE email = %s AND password_hash = %s", (email, password))
            usuario = cursor.fetchone()
            
            if usuario:
                token = str(uuid.uuid4())
                redis_client.setex(token, 86400, usuario['id'])
                return jsonify({"mensaje": "Bienvenido al panel", "token": token, "rol": usuario['rol']}), 200
            else:
                return jsonify({"error": "Correo o contraseña incorrectos"}), 401
    finally:
        conexion.close()

# --- FUNCIÓN AUXILIAR: Formatear Fechas ---
def sanitizar_fechas(registro):
    for key, value in registro.items():
        if hasattr(value, 'isoformat'):
            registro[key] = value.isoformat()
    return registro


@app.route('/')
def index():
    return jsonify({"mensaje": "¡Bienvenido a la API de AdoptMe!"})


# ==========================================
# MÓDULO 1: MASCOTAS
# ==========================================

@app.route('/agregar', methods=['POST'])
@requiere_admin # <-- RUTA PROTEGIDA
def agregar_mascota():
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se enviaron datos"}), 400

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """INSERT INTO mascotas 
                     (nombre, especie, raza, fecha_nacimiento_aprox, tamano, sexo, energia, salud, estado_adopcion, notas_medicas) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            valores = (
                datos.get('nombre'), datos.get('especie'), datos.get('raza', 'Mestizo'),
                datos.get('fecha_nacimiento_aprox'), datos.get('tamano'), datos.get('sexo'), 
                datos.get('energia', 'Media'), datos.get('salud'),
                datos.get('estado_adopcion', 'disponible'), datos.get('notas_medicas', '')
            )
            cursor.execute(sql, valores)
        conexion.commit()
        return jsonify({"mensaje": "Mascota registrada", "id_asignado": cursor.lastrowid}), 201
    except pymysql.err.IntegrityError as e:
        return jsonify({"error": "Faltan datos obligatorios o hay un error de formato", "detalle": str(e)}), 400
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
@requiere_admin # <-- RUTA PROTEGIDA
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
                datos.get('password'), datos.get('telefono'), datos.get('rol', 'adoptante')
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
            cursor.execute("SELECT id, nombre_completo, email, telefono, rol, activo, creado_en FROM usuarios")
            usuarios = [sanitizar_fechas(u) for u in cursor.fetchall()]
        return jsonify(usuarios), 200
    finally:
        conexion.close()


# ==========================================
# MÓDULO 3: SOLICITUDES
# ==========================================

@app.route('/solicitudes', methods=['POST'])
@requiere_login # <--- MAGIA: Protegemos la ruta e inyectamos el usuario_id verificado
def crear_solicitud(usuario_id):
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se enviaron datos"}), 400
        
    mascota_id = datos.get('mascota_id')
    datos_formulario = datos.get('datos_formulario') # Aquí viene el objeto con las 40 preguntas
    
    if not mascota_id or not datos_formulario:
        return jsonify({"error": "Faltan campos obligatorios (mascota_id o datos_formulario)"}), 400
        
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Verificamos que la mascota exista y esté disponible
            cursor.execute("SELECT estado_adopcion FROM mascotas WHERE id = %s", (mascota_id,))
            mascota = cursor.fetchone()
            if not mascota:
                return jsonify({"error": "La mascota especificada no existe."}), 404
            if mascota['estado_adopcion'] != 'disponible':
                return jsonify({"error": "Esta mascota ya no se encuentra disponible para adopción."}), 400

            # Insertamos la solicitud vinculando el usuario_id de la sesión activa
            sql = """INSERT INTO solicitudes (usuario_id, mascota_id, datos_formulario, estado) 
                     VALUES (%s, %s, %s, 'pendiente')"""
            
            # json.dumps convierte el diccionario de respuestas del formulario en un string estructurado para MySQL
            cursor.execute(sql, (usuario_id, mascota_id, json.dumps(datos_formulario)))
            
            # Opcional: Cambiamos el estado de la mascota a 'en_proceso' para que nadie más la aplique por ahora
            cursor.execute("UPDATE mascotas SET estado_adopcion = 'en_proceso' WHERE id = %s", (mascota_id,))
            
        conexion.commit()
        return jsonify({"mensaje": "¡Solicitud de adopción recibida con éxito! El equipo revisará tu perfil."}), 201
    except Exception as e:
        conexion.rollback()
        return jsonify({"error": "Error interno al procesar la solicitud", "detalle": str(e)}), 500
    finally:
        conexion.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)