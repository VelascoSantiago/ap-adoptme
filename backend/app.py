from flask import Flask, jsonify, request
from pymongo import MongoClient
import redis

app = Flask(__name__)

# --- CONEXIÓN A MONGODB ---
# Usamos 'mongodb' como host porque es el nombre del servicio en el docker-compose.yml
mongo_client = MongoClient("mongodb://mongodb:27017/")
db = mongo_client["adoptme_db"] # Si la BD no existe, Mongo la creará al vuelo

# Definimos nuestras colecciones (el equivalente a tus tablas en MySQL)
mascotas_collection = db["mascotas"]
usuarios_collection = db["usuarios"]
solicitudes_collection = db["solicitudes"]

# --- CONEXIÓN A REDIS ---
# Usamos 'redis' como host por la misma razón
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# --- ENDPOINT DE PRUEBA ---
@app.route('/')
def index():
    return jsonify({
        "mensaje": "¡Bienvenido a la API de AdoptMe!",
        "estado": "El backend está conectado y funcionando."
    })

if __name__ == '__main__':
    # debug=True nos permite ver los cambios en tiempo real sin reiniciar el contenedor
    app.run(host='0.0.0.0', port=8000, debug=True)
