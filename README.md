# Attendance Management API

Una API moderna y robusta para gestionar la asistencia de empleados utilizando FastAPI y mejores prácticas de desarrollo.

## 🚀 Características

- **API RESTful** con FastAPI
- **Autenticación JWT** para seguridad
- **Validación de datos** con Pydantic
- **Manejo robusto de errores** con reintentos automáticos
- **Logging estructurado** para monitoreo
- **Dockerizado** para fácil deployment
- **Tests automatizados** con pytest
- **Documentación automática** con Swagger/OpenAPI

## 📋 Requisitos

- Python 3.11+
- Docker (opcional)
- Redis (para caché, opcional)

## 🛠️ Instalación

### Instalación Local

```bash
# Clonar el repositorio
git clone <repository-url>
cd attendance-api

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Instalar dependencias
make install
# o pip install -r requirements.txt

# Configurar variables de entorno
make setup-env
# Editar .env con tu configuración
```

### Instalación con Docker

```bash
# Construir y ejecutar
make docker-run

# O manualmente
docker-compose up -d
```

## ⚙️ Configuración

Crea un archivo `.env` basado en `.env.example`:

```bash
BASE_URL=https://movil.asisscad.cl
COMPANY_ID=7040
REQUEST_TIMEOUT=30
MAX_RETRIES=3
JWT_SECRET_KEY=tu-clave-secreta-super-segura
JWT_ALGORITHM=HS256
```

## 🚀 Uso

### Ejecutar localmente

```bash
make run
# o
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Ejecutar con Docker

```bash
make docker-run
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📚 Endpoints de la API

### Marcar Asistencia

```bash
POST /api/v1/attendance
```

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
  "credentials": {
    "user_id": 77668171,
    "password": "tu_password"
  },
  "location": {
    "latitude": -6.7711,
    "longitude": -79.8431
  },
  "action": "lnk_entrada"
}
```

**Respuesta:**
```json
{
  "success": true,
  "message": "Attendance marked successfully",
  "action": "lnk_entrada",
  "timestamp": "2025-08-14T10:30:00",
  "location": {
    "latitude": -6.7711,
    "longitude": -79.8431
  }
}
```

### Health Check

```bash
GET /api/v1/health
```

### Crear Token de Autenticación

```bash
POST /api/v1/auth/token
```

## 🧪 Testing

```bash
# Ejecutar tests
make test

# Tests con cobertura
make test

# Tests en modo watch
make test-watch

# Linting
make lint

# Formateo de código
make format
```

## 📁 Estructura del Proyecto

```
attendance-api/
├── api/
│   └── routes.py          # Endpoints de la API
├── services/
│   ├── attendance_service.py  # Lógica de asistencia
│   └── auth_service.py    # Lógica de autenticación
├── tests/
│   └── test_attendance.py # Tests unitarios
├── config.py              # Configuración
├── models.py              # Modelos Pydantic
├── exceptions.py          # Excepciones personalizadas
├── main.py               # Aplicación FastAPI
├── requirements.txt      # Dependencias
├── Dockerfile           # Imagen Docker
├── docker-compose.yml   # Orquestación
├── nginx.conf          # Configuración Nginx
├── Makefile            # Comandos de desarrollo
└── README.md           # Documentación
```

## 🔒 Seguridad

- **Autenticación JWT** para todos los endpoints
- **Validación de entrada** con Pydantic
- **Rate limiting** con Nginx
- **Headers de seguridad** configurados
- **HTTPS** recomendado en producción

## 🚀 Deployment

### Docker Compose (Recomendado)

```bash
# Producción
docker-compose up -d

# Ver logs
make docker-logs

# Parar servicios
make docker-stop
```

### Kubernetes

```yaml
# Ejemplo de deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: attendance-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: attendance-api
  template:
    metadata:
      labels:
        app: attendance-api
    spec:
      containers:
      - name: attendance-api
        image: attendance-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: BASE_URL
          value: "https://movil.asisscad.cl"
        - name: COMPANY_ID
          value: "7040"
```

## 📊 Monitoreo

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Logs

```bash
# Docker logs
make docker-logs

# Logs locales
tail -f logs/app.log
```

### Métricas

La API incluye endpoints para monitoreo:
- `/api/v1/health` - Estado de salud
- `/metrics` - Métricas de Prometheus (opcional)

## 🛠️ Comandos de Desarrollo

```bash
# Ver todos los comandos disponibles
make help

# Desarrollo
make dev              # Instalar deps de desarrollo
make run              # Ejecutar localmente
make test             # Ejecutar tests
make lint             # Linting
make format           # Formatear código

# Docker
make docker-build     # Construir imagen
make docker-run       # Ejecutar con compose
make docker-stop      # Parar contenedores
make docker-logs      # Ver logs

# Utilidades
make clean            # Limpiar archivos cache
make security-scan    # Escaneo de seguridad
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request

## 📝 Changelog

### v1.0.0
- ✅ API inicial con FastAPI
- ✅ Autenticación JWT
- ✅ Manejo de asistencia
- ✅ Tests unitarios
- ✅ Dockerización
- ✅ Documentación completa

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

Si encuentras algún problema o tienes preguntas:

1. Revisa la [documentación](http://localhost:8000/docs)
2. Busca en los [issues existentes](../../issues)
3. Crea un [nuevo issue](../../issues/new) si es necesario

## 🔗 Enlaces Útiles

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
- [Docker Documentation](https://docs.docker.com/)
- [pytest Documentation](https://docs.pytest.org/)