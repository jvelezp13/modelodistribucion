# 🚀 Guía de Deployment - Sistema DxV Full Stack

Esta guía te llevará paso a paso para desplegar el sistema completo (Django + FastAPI + Next.js + PostgreSQL) en Easypanel.

---

## 📋 Tabla de Contenidos

1. [Preparación Inicial](#1-preparación-inicial)
2. [Configuración de Base de Datos](#2-configuración-de-base-de-datos)
3. [Despliegue del Backend (Django Admin)](#3-despliegue-del-backend-django-admin)
4. [Despliegue de la API (FastAPI)](#4-despliegue-de-la-api-fastapi)
5. [Despliegue del Frontend (Next.js)](#5-despliegue-del-frontend-nextjs)
6. [Migración de Datos](#6-migración-de-datos)
7. [Solución de Problemas](#7-solución-de-problemas)

---

## 1. Preparación Inicial

### Requisitos Previos
- ✅ Cuenta en Easypanel
- ✅ Proyecto creado en Easypanel
- ✅ Repositorio Git accesible

### Arquitectura de Servicios
Desplegaremos 4 servicios interconectados:
1. **PostgreSQL**: Base de datos central
2. **Django Admin**: Gestión de datos (`admin_panel/`)
3. **FastAPI**: Lógica de negocio y API (`api/`)
4. **Next.js**: Interfaz de usuario (`frontend/`)

---

## 2. Configuración de Base de Datos

1. En Easypanel, ve a **Databases** → **Create Database**
2. Selecciona **PostgreSQL 15**
3. Configura:
   - **Name**: `dxv_postgres`
   - **Username**: `postgres`
   - **Password**: (genera una segura)
   - **Database Name**: `dxv_db`
4. **IMPORTANTE**: Guarda las credenciales, las usarás en todos los servicios.

---

## 3. Despliegue del Backend (Django Admin)

Este servicio maneja la administración y las migraciones de la base de datos.

1. **Create App** → **From Git Repository**
2. Configuración:
   - **Repository**: `tu-repo/modelodistribucion`
   - **Branch**: `main`
   - **Dockerfile Path**: `admin_panel/Dockerfile`
   - **Port**: `8000`

3. **Variables de Entorno**:
   ```env
   DJANGO_SECRET_KEY=tu-secret-key-segura
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=tu-dominio-admin.com,*.easypanel.host
   POSTGRES_DB=dxv_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=tu-password-db
   POSTGRES_HOST=dxv_postgres
   POSTGRES_PORT=5432
   ```

4. **Deploy**

5. **Post-Deployment**:
   - Abre la terminal del servicio y ejecuta:
     ```bash
     python manage.py migrate
     python manage.py createsuperuser
     ```

---

## 4. Despliegue de la API (FastAPI)

Este servicio expone la lógica de simulación al frontend.

1. **Create App** → **From Git Repository**
2. Configuración:
   - **Repository**: `tu-repo/modelodistribucion`
   - **Dockerfile Path**: `Dockerfile.api`
   - **Port**: `8000`

3. **Variables de Entorno**:
   ```env
   POSTGRES_DB=dxv_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=tu-password-db
   POSTGRES_HOST=dxv_postgres
   POSTGRES_PORT=5432
   ALLOWED_ORIGINS=https://tu-dominio-frontend.com
   ```

4. **Deploy**

---

## 5. Despliegue del Frontend (Next.js)

La nueva interfaz de usuario moderna.

1. **Create App** → **From Git Repository**
2. Configuración:
   - **Repository**: `tu-repo/modelodistribucion`
   - **Dockerfile Path**: `frontend/Dockerfile`
   - **Port**: `3000`

3. **Variables de Entorno**:
   ```env
   NEXT_PUBLIC_API_URL=https://tu-dominio-api.com
   ```

4. **Deploy**

---

## 6. Migración de Datos

Para cargar los datos iniciales desde los archivos YAML:

1. Ve a la terminal del servicio **Django Admin**
2. Ejecuta:
   ```bash
   python manage.py import_from_yaml --data-path=../data --config-path=../config
   ```

---

## 7. Solución de Problemas

### Error de Conexión a DB
Verifica que `POSTGRES_HOST` sea el nombre exacto del servicio de base de datos en Easypanel (usualmente el nombre que le diste al crearlo).

### CORS Error en Frontend
Asegúrate de que la variable `ALLOWED_ORIGINS` en la API incluya el dominio de tu frontend (sin trailing slash).

### Archivos Estáticos en Django
Si no cargan los estilos del admin, asegúrate de que `python manage.py collectstatic` se ejecute en el build o start command (el Dockerfile ya debería manejarlo).

