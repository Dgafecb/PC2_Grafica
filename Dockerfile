# Usa una imagen de Python más ligera
FROM python:3.10-slim

# Instala dependencias del sistema necesarias para scikit-image y otros paquetes
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libffi-dev \
    libgl1-mesa-glx \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libtiff-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo
WORKDIR /app

# Copia el archivo requirements.txt
COPY requirements.txt .

# Instala las dependencias de Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia el resto de la aplicación
COPY . .

# Expone el puerto de la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app"]
