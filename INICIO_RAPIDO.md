# 🚀 Inicio Rápido
 
 Esta guía te ayudará a poner en marcha el sistema de distribución multimarcas en minutos usando Docker.
 
 ---
 
 ## 📋 Requisitos Previos
 
 - **Docker** y **Docker Compose** instalados en tu sistema.
 - **Git**
 
 ---
 
 ## ⚡ Instalación Rápida (Recomendada)
 
 La forma más fácil de iniciar el sistema completo (Base de Datos + Admin + Frontend + Dashboard) es con Docker.
 
 ### 1. Clonar el repositorio
 
 ```bash
 git clone https://github.com/jvelezp13/modelodistribucion.git
 cd modelodistribucion
 ```
 
 ### 2. Iniciar servicios
 
 ```bash
 docker-compose up --build
 ```
 
 Espera unos minutos mientras se construyen las imágenes y se inician los contenedores.
 
 ### 3. Cargar datos iniciales
 
 Una vez que los servicios estén corriendo (verás logs en la terminal), abre una **nueva terminal** y ejecuta:
 
 ```bash
 docker-compose exec django_admin python manage.py import_from_yaml
 ```
 
 Esto poblará la base de datos con la configuración y marcas de ejemplo definidas en los archivos YAML.
 
 ---
 
 ## 🎯 Acceder a la Aplicación
 
 Una vez iniciado, tendrás acceso a:
 
 | Componente | URL | Descripción |
 |------------|-----|-------------|
 | **Frontend (Nuevo)** | `http://localhost:3000` | Nueva interfaz de usuario moderna |
 | **Admin Panel** | `http://localhost:8000/admin` | Gestión de datos maestros |
 | **Legacy Dashboard** | `http://localhost:8501` | Dashboard original (Streamlit) |
 | **API Docs** | `http://localhost:8001/docs` | Documentación de la API |
 
 **Credenciales por defecto (Admin Panel):**
 - Debes crear un superusuario primero:
   ```bash
   docker-compose exec django_admin python manage.py createsuperuser
   ```
 
 ---
 
 ## 🔧 Desarrollo Local (Legacy / Sin Docker)
 
 > ⚠️ **Advertencia:** Este método es más complejo ya que requiere configurar una base de datos PostgreSQL localmente.
 
 ### 1. Configurar PostgreSQL Local
 
 Asegúrate de tener PostgreSQL corriendo y crea una base de datos llamada `dxv_db`.
 
 ### 2. Configurar Variables de Entorno
 
 Crea un archivo `.env` en la raíz:
 
 ```env
 POSTGRES_DB=dxv_db
 POSTGRES_USER=tu_usuario
 POSTGRES_PASSWORD=tu_password
 POSTGRES_HOST=localhost
 POSTGRES_PORT=5432
 ```
 
 ### 3. Instalar Dependencias
 
 ```bash
 python3 -m venv venv
 source venv/bin/activate
 pip install -r requirements.txt
 ```
 
 ### 4. Inicializar Base de Datos
 
 ```bash
 # Aplicar migraciones
 cd admin_panel
 python manage.py migrate
 
 # Cargar datos
 python manage.py import_from_yaml --data-path=../data --config-path=../config
 ```
 
 ### 5. Ejecutar Dashboard
 
 ```bash
 cd ..
 streamlit run panels/app.py
 ```

