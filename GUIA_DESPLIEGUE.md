# 🚀 Guía de Despliegue - Sistema DxV Multimarcas

Esta guía cubre todo lo necesario para desplegar el sistema, tanto en entorno local (Docker Compose) como en producción (Easypanel).

---

## 📋 Tabla de Contenidos

1. [Arquitectura de Despliegue](#1-arquitectura-de-despliegue)
2. [Variables de Entorno](#2-variables-de-entorno)
3. [Desarrollo Local (Docker Compose)](#3-desarrollo-local-docker-compose)
4. [Despliegue en Producción (Easypanel)](#4-despliegue-en-producción-easypanel)
5. [Solución de Problemas](#5-solución-de-problemas)

---

## 1. Arquitectura de Despliegue

El sistema consta de 4 servicios principales que deben desplegarse juntos:

1.  **Base de Datos (PostgreSQL):** Puerto 5432. Fuente de verdad.
2.  **Backend Admin (Django):** Puerto 8000. Gestión de datos y migraciones.
3.  **API (FastAPI):** Puerto 8001 (o 8000 interno). Lógica de simulación.
4.  **Frontend (Next.js):** Puerto 3000. Interfaz de usuario.

---

## 2. Variables de Entorno

Crea un archivo `.env` (local) o configura estas variables en tu plataforma de hosting.

### Base de Datos
```bash
POSTGRES_DB=nexo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_password_seguro
POSTGRES_HOST=postgres  # 'localhost' si corres sin docker, o el nombre del servicio en Easypanel
POSTGRES_PORT=5432
```

### Django (Admin)
```bash
DJANGO_SECRET_KEY=tu_secret_key_larga_y_segura
DJANGO_DEBUG=False  # True solo en desarrollo
DJANGO_ALLOWED_HOSTS=*,localhost,tu-dominio.com
```

### Frontend
```bash
# URL pública de la API (accesible desde el navegador del usuario)
NEXT_PUBLIC_API_URL=http://localhost:8001  # O https://api.tu-dominio.com en producción
```

---

## 3. Desarrollo Local (Docker Compose)

La forma más rápida de probar el sistema completo.

### Requisitos
- Docker y Docker Compose instalados.

### Pasos
1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/jvelezp13/modelodistribucion.git
   cd modelodistribucion
   ```

2. **Crear archivo .env:**
   Copia el ejemplo o usa las variables mencionadas arriba.

3. **Iniciar servicios:**
   ```bash
   docker-compose up --build
   ```

4. **Acceder:**
   - Frontend: http://localhost:3000
   - Admin: http://localhost:8000/admin
   - API Docs: http://localhost:8001/docs

5. **Cargar Datos Iniciales (Opcional):**
   ```bash
   docker-compose exec django_admin python manage.py import_from_yaml
   ```

---

## 4. Despliegue en Producción (Easypanel)

Guía para desplegar en un servidor con Easypanel.

### Paso 1: Base de Datos
1. Crea un servicio **Database** (PostgreSQL 15).
2. Nombre: `dxv_db`.
3. Guarda las credenciales (Host, User, Password, DB Name).

### Paso 2: Backend (Django)
1. Crea un servicio **App** desde GitHub.
2. **Build Path:** `admin_panel`
3. **Port:** 8000
4. **Env Vars:** Configura las variables de BD y Django.

### Paso 3: API (FastAPI)
1. Crea un servicio **App** desde GitHub.
2. **Dockerfile:** `Dockerfile.api`
3. **Port:** 8000 (interno del contenedor)
4. **Env Vars:** Mismas variables de BD que Django.
5. **Dominio:** Asigna un dominio (ej. `api.tu-dominio.com`).

### Paso 4: Frontend (Next.js)
1. Crea un servicio **App** desde GitHub.
2. **Build Path:** `frontend`
3. **Port:** 3000
4. **Env Vars:**
   - `NEXT_PUBLIC_API_URL`: `https://api.tu-dominio.com` (La URL del paso 3).
5. **Dominio:** Asigna tu dominio principal (ej. `tu-dominio.com`).

### Paso 5: Migraciones
Una vez desplegado Django, abre la consola del servicio y ejecuta:
```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## 5. Solución de Problemas

### Frontend no conecta con API
- Verifica que `NEXT_PUBLIC_API_URL` en el Frontend apunte a la URL **pública** (HTTPS) de la API, no a `localhost` ni a la IP interna de Docker, ya que esta petición se hace desde el navegador del usuario.

### Error de Base de Datos
- Asegúrate de que todos los servicios (Django, API) tengan las mismas credenciales de conexión.
- En Easypanel, usa el **Internal Host** de la base de datos para menor latencia.

### Archivos Estáticos en Django
- Si no cargan los estilos del Admin, asegúrate de configurar `WHITENOISE` o servir los estáticos correctamente (ya configurado en `settings.py` para producción).
