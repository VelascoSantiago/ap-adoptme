# Usamos una imagen ligera de Python
FROM python:3.10-slim

# Establecemos el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiamos las dependencias y las instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo nuestro código de Flask
COPY . .

# Exponemos el puerto donde correrá Flask
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["flask", "--app", "app.py", "run", "--host=0.0.0.0", "--port=8000"]
