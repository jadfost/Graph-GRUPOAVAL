# DjangoDocker

Este proyecto es una configuración básica de Docker para una aplicación Django. Sigue los pasos a continuación para configurar y ejecutar el proyecto en tu máquina local.

## [🚀 Ver la documentación de Docker](https://docs.docker.com/)

Estas integraciones trabajan juntas para simplificar el desarrollo y mejorar la experiencia del usuario.

### Instrucciones de Configuración

Sigue estos pasos para configurar y ejecutar este proyecto en tu máquina local:

1. Clona este repositorio en tu máquina local:

```bash
git clone https://github.com/{perfil}/DjangoDocker.git
cd DjangoDocker
```

2. Construye la imagen Docker utilizando Docker Compose. Este paso instalará todas las dependencias definidas en requirements.txt y configurará el entorno dentro de un contenedor:

```bash
    docker-compose build
```

3. Inicia el contenedor que ejecutará el servidor de desarrollo de Django:

```bash
    docker-compose up
```

4. Esto lanzará la aplicación en local:

```bash
    Abre tu navegador y ve a http://localhost:8000
```

## Comandos Útiles

1. Detener y eliminar contenedores: Para detener el contenedor y eliminarlo junto con la red asociada, utiliza:

```bash
    docker-compose down
```

2. Acceder al contenedor: Si necesitas acceder al contenedor en ejecución para depuración o inspección:

```bash
    docker exec -it djangodocker-web-1 /bin/sh
```

## Problemas Comunes

Error de archivo no encontrado (manage.py): Si el contenedor no puede encontrar el archivo manage.py, asegúrate de que el volumen esté montado correctamente en docker-compose.yml:

```bash
volumes:
  - ./app:/app
```
