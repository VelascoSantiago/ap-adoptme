from flask import Flask, jsonify, request
import pymysql
import redis
import time

app = Flask(__name__)

# --- CONEXIÓN A MYSQL (Con reintentos por si tarda en arrancar) ---
def obtener_conexion():
    retries = 5
    while retries > 0:
        try:
            conexion = pymysql.connect(
                host='mysql',
                user='root',
                password='root',
                database='adoptme_db',
                cursorclass=pymysql.cursors.DictCursor # Hace que los SELECT devuelvan diccionarios (JSON)
            )
            return conexion
        except pymysql.MySQLError as e:
            retries -= 1
            time.sleep(2) # Espera 2 segundos antes de reintentar
    raise Exception("No se pudo conectar a la base de datos.")

# --- CONEXIÓN A REDIS ---
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

@app.route('/')
def index():
    return jsonify({
        "mensaje": "¡Bienvenido a la API de AdoptMe!",
        "estado": "El backend está conectado a MySQL y funcionando."
    })

# --- CASO DE USO 1: Registrar Mascota ---
@app.route('/agregar', methods=['POST'])
def agregar_mascota():
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se enviaron datos"}), 400

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Consulta SQL preparada (evita inyecciones SQL)
            sql = """INSERT INTO mascotas 
                     (nombre, especie, raza, fecha_nacimiento_aprox, tamano, salud, estado_adopcion, notas_medicas) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            
            # Usamos .get() para manejar campos opcionales sin que Python lance error
            valores = (
                datos.get('nombre'),
                datos.get('especie'),
                datos.get('raza', 'Mestizo'),
                datos.get('fecha_nacimiento_aprox'),
                datos.get('tamano'),
                datos.get('salud'),
                datos.get('estado_adopcion', 'disponible'),
                datos.get('notas_medicas', '')
            )
            cursor.execute(sql, valores)
        conexion.commit() # Confirmamos la transacción
        nuevo_id = cursor.lastrowid # Obtenemos el ID auto-incremental generado
        
        return jsonify({
            "mensaje": "Mascota registrada correctamente",
            "id_asignado": nuevo_id
        }), 201
    finally:
        conexion.close() # Siempre cerrar la conexión

# --- CASO DE USO 2: Visualizar Mascotas ---
@app.route('/mascotas', methods=['GET'])
def ver_mascotas():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM mascotas")
            lista_mascotas = cursor.fetchall()
            
            # Formateamos las fechas a string para que Flask las pueda convertir a JSON
            for mascota in lista_mascotas:
                if mascota.get('fecha_nacimiento_aprox'):
                    mascota['fecha_nacimiento_aprox'] = str(mascota['fecha_nacimiento_aprox'])
                if mascota.get('creado_en'):
                    mascota['creado_en'] = str(mascota['creado_en'])
                if mascota.get('actualizado_en'):
                    mascota['actualizado_en'] = str(mascota['actualizado_en'])

        return jsonify(lista_mascotas), 200
    finally:
        conexion.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
