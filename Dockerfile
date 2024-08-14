# Usa una imagen base oficial de Python
FROM python:3.10-slim

# Establece el directorio de trabajo en el contenedor
WORKDIR /app

# Copia el archivo de requerimientos al contenedor
COPY requirements.txt .

# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el código del proyecto al contenedor
COPY . .

# Exponer el puerto en el que correrá la aplicación si es necesario
EXPOSE 8000

# Comando por defecto para ejecutar tu script
CMD ["python", "app/GraphApi.py"]
