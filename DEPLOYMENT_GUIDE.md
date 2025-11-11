# 🚀 Guía de Deployment - Sistema DxV con PostgreSQL

Esta guía te llevará paso a paso para desplegar el sistema completo en Easypanel con PostgreSQL.

---

## 📋 Tabla de Contenidos

1. [Preparación Inicial](#1-preparación-inicial)
2. [Configuración en Easypanel](#2-configuración-en-easypanel)
3. [Migración de Datos YAML → PostgreSQL](#3-migración-de-datos)
4. [Acceso al Panel Admin](#4-acceso-al-panel-admin)
5. [Configuración del Dashboard Streamlit](#5-dashboard-streamlit)
6. [Solución de Problemas](#6-solución-de-problemas)

---

## 1. Preparación Inicial

### Requisitos Previos
- ✅ Cuenta en Easypanel
- ✅ PostgreSQL configurado en Easypanel
- ✅ Git configurado localmente

### Archivos Necesarios
El sistema incluye:
```
modelodistribucion/
├── admin_panel/          # Panel Django Admin
│   ├── dxv_admin/       # Configuración Django
│   ├── core/            # Modelos y admin
│   ├── Dockerfile       # Para deployment
│   └── requirements.txt
├── panels/              # Dashboard Streamlit
├── utils/               # Utilidades (DataLoader)
├── docker-compose.yml   # Para desarrollo local
└── .env.example         # Variables de entorno
```

---

## 2. Configuración en Easypanel

### Paso 1: Crear Base de Datos PostgreSQL

1. En Easypanel, ve a **Databases** → **Create Database**
2. Selecciona **PostgreSQL 15**
3. Configura:
   - **Name**: `dxv_postgres`
   - **Username**: `postgres`
   - **Password**: (genera una segura)
   - **Database Name**: `dxv_db`
4. Copia las credenciales (las necesitarás después)

### Paso 2: Desplegar Django Admin Panel

1. En Easypanel, ve a **Apps** → **Create App**
2. Selecciona **From Git Repository**
3. Configuración:
   - **Repository**: `tu-repo/modelodistribucion`
   - **Branch**: `claude/design-simple-panels-011CV13BN5D4RTTUSiVRnWaG`
   - **Dockerfile Path**: `admin_panel/Dockerfile`
   - **Port**: `8000`

4. **Variables de Entorno** (muy importante):
   ```env
   DJANGO_SECRET_KEY=tu-secret-key-aqui-genera-una-segura
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=tu-dominio.com,*.easypanel.host
   POSTGRES_DB=dxv_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=tu-password-de-postgresql
   POSTGRES_HOST=dxv_postgres  # Nombre del servicio PostgreSQL en Easypanel
   POSTGRES_PORT=5432
   ```

5. Click en **Deploy**

### Paso 3: Ejecutar Migraciones

Una vez desplegado, necesitas crear las tablas en PostgreSQL:

1. Abre la **Terminal** del contenedor Django en Easypanel
2. Ejecuta:
   ```bash
   python manage.py migrate
   ```

3. Crea un superusuario para acceder al admin:
   ```bash
   python manage.py createsuperuser
   ```
   - Email: tu-email@ejemplo.com
   - Password: (elige una segura)

---

## 3. Migración de Datos

### Importar Datos desde YAML a PostgreSQL

Tienes 2 opciones:

#### Opción A: Desde el Contenedor en Easypanel

1. Abre la **Terminal** del contenedor Django
2. Ejecuta el comando de importación:
   ```bash
   python manage.py import_from_yaml --data-path=../data --config-path=../config
   ```

3. Verás el progreso:
   ```
   === Iniciando Importación desde YAML ===

   [1/6] Importando parámetros macroeconómicos...
     ✓ Parámetros 2025 creados

   [2/6] Importando factores prestacionales...
     ✓ Factor comercial creado
     ✓ Factor administrativo creado
     ✓ Factor logistico creado

   [3/6] Importando marcas...
     ✓ Marca Nutresa creada
     ✓ Marca Ejemplo creada

   [4/6] Importando datos de marcas...
     Procesando marca: Nutresa
       ✓ 7 registros de personal comercial importados
       ✓ 12 vehículos importados
       ✓ 23 registros de personal logístico importados
       ✓ Volumen de operación importado
       ✓ 12 proyecciones de ventas importadas

   ✅ Importación completada exitosamente
   ```

#### Opción B: Desde tu Mac Local

1. Configura las variables de entorno:
   ```bash
   export POSTGRES_HOST=tu-postgres-host.easypanel.host
   export POSTGRES_DB=dxv_db
   export POSTGRES_USER=postgres
   export POSTGRES_PASSWORD=tu-password
   export POSTGRES_PORT=5432
   ```

2. Ejecuta la importación:
   ```bash
   cd admin_panel
   python manage.py import_from_yaml
   ```

---

## 4. Acceso al Panel Admin

### URL de Acceso
Una vez desplegado, accede a:
```
https://tu-app.easypanel.host/admin/
```

### Primer Login
1. Usa el superusuario que creaste
2. Verás el panel con todas las secciones:
   - **Marcas**
   - **Personal Comercial**
   - **Personal Logístico**
   - **Vehículos**
   - **Proyecciones de Ventas**
   - **Volumen de Operación**
   - **Parámetros Macroeconómicos**
   - **Factores Prestacionales**

### Ejemplo de Uso

**Agregar un Vendedor:**
1. Click en **Personal Comercial** → **Agregar**
2. Completa el formulario:
   - Marca: Nutresa
   - Tipo: Vendedor Geográfico
   - Cantidad: 1
   - Salario Base: 2,800,000
   - Perfil: Comercial
   - Asignación: Individual
3. **Guardar**

**Modificar Ventas:**
1. Click en **Proyecciones de Ventas**
2. Busca "Nutresa - Enero 2025"
3. Click en **Editar**
4. Cambia el valor de ventas
5. **Guardar**

---

## 5. Dashboard Streamlit

### Desplegar Dashboard en Easypanel

1. En Easypanel, **Create App** → **From Git Repository**
2. Configuración:
   - **Dockerfile Path**: `Dockerfile.streamlit`
   - **Port**: `8501`

3. **Variables de Entorno**:
   ```env
   POSTGRES_DB=dxv_db
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=tu-password
   POSTGRES_HOST=dxv_postgres
   POSTGRES_PORT=5432
   ```

4. **Deploy**

### Cambiar DataLoader para Usar PostgreSQL

Actualiza `/home/user/modelodistribucion/panels/app.py`:

Cambia la línea:
```python
from utils.loaders import get_loader
```

Por:
```python
from utils.loaders_db import get_loader_db as get_loader
```

Esto hará que el dashboard lea de PostgreSQL en lugar de YAML.

---

## 6. Solución de Problemas

### Error: "No module named 'django'"
**Solución**: Asegúrate de que el Dockerfile incluye:
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

### Error: "FATAL: password authentication failed"
**Solución**: Verifica que las credenciales de PostgreSQL sean correctas en las variables de entorno.

### Error: "relation 'core_marca' does not exist"
**Solución**: Ejecuta las migraciones:
```bash
python manage.py migrate
```

### El Dashboard no muestra datos
**Solución**:
1. Verifica que la importación YAML→PostgreSQL se completó
2. Asegúrate de que el dashboard usa `loaders_db.py`
3. Verifica la conexión a PostgreSQL

---

## 🎯 Flujo de Trabajo Completo

### Edición de Datos
1. **Abres el Panel Admin** → `https://tu-app.easypanel.host/admin/`
2. **Editas datos** (vendedores, vehículos, ventas, etc.)
3. **Guardas los cambios** (se guardan automáticamente en PostgreSQL)

### Visualización
1. **Abres el Dashboard Streamlit** → `https://tu-dashboard.easypanel.host/`
2. **Seleccionas marcas** a simular
3. **Click en "Ejecutar Simulación"**
4. **Ves los resultados** actualizados con los datos de PostgreSQL

### Backup de Datos
Para hacer backup de PostgreSQL en Easypanel:
```bash
pg_dump -h dxv_postgres -U postgres -d dxv_db > backup.sql
```

---

## 📞 Soporte

Si tienes problemas, revisa:
1. Logs del contenedor Django en Easypanel
2. Logs de PostgreSQL
3. Variables de entorno configuradas

---

## 🎉 ¡Listo!

Ahora tienes:
- ✅ Panel Admin Django funcionando
- ✅ PostgreSQL con todos los datos
- ✅ Dashboard Streamlit conectado
- ✅ Edición fácil desde el navegador

**No más YAMLs manuales** 🚀
