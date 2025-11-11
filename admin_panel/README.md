# Django Admin Panel - Sistema DxV

Panel de administración web para gestionar el sistema de Distribución y Ventas (DxV).

## 🚀 Inicio Rápido

### Desarrollo Local

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar variables de entorno**:
   ```bash
   export POSTGRES_HOST=localhost
   export POSTGRES_DB=dxv_db
   export POSTGRES_USER=postgres
   export POSTGRES_PASSWORD=postgres
   ```

3. **Ejecutar migraciones**:
   ```bash
   python manage.py migrate
   ```

4. **Crear superusuario**:
   ```bash
   python manage.py createsuperuser
   ```

5. **Importar datos desde YAML**:
   ```bash
   python manage.py import_from_yaml
   ```

6. **Iniciar servidor**:
   ```bash
   python manage.py runserver
   ```

7. **Acceder al admin**: http://localhost:8000/admin/

## 📦 Estructura

```
admin_panel/
├── dxv_admin/              # Configuración del proyecto Django
│   ├── settings.py         # Settings (PostgreSQL config)
│   ├── urls.py             # URLs
│   ├── wsgi.py             # WSGI app
│   └── asgi.py             # ASGI app
├── core/                   # App principal
│   ├── models.py           # Modelos de BD
│   ├── admin.py            # Configuración Django Admin
│   └── management/         # Commands personalizados
│       └── commands/
│           └── import_from_yaml.py
├── manage.py               # Django CLI
├── requirements.txt        # Dependencias Python
└── Dockerfile              # Para deployment
```

## 🗄️ Modelos

- **Marca**: Marcas del sistema
- **PersonalComercial**: Vendedores, supervisores, coordinadores
- **PersonalLogistico**: Conductores, auxiliares, operarios
- **Vehiculo**: Flota de vehículos (renting/tradicional)
- **ProyeccionVentas**: Ventas mensuales por marca
- **VolumenOperacion**: Volumen logístico
- **ParametrosMacro**: IPC, salarios, subsidios
- **FactorPrestacional**: Factores prestacionales por perfil

## 🔧 Management Commands

### Importar desde YAML
```bash
python manage.py import_from_yaml --data-path=../data --config-path=../config
```

### Crear migraciones
```bash
python manage.py makemigrations
```

### Aplicar migraciones
```bash
python manage.py migrate
```

## 🐳 Docker

### Build
```bash
docker build -t dxv-admin .
```

### Run
```bash
docker run -p 8000:8000 \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_DB=dxv_db \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  dxv-admin
```

## 📝 Variables de Entorno

- `DJANGO_SECRET_KEY`: Secret key (requerido en producción)
- `DJANGO_DEBUG`: True/False (default: True)
- `DJANGO_ALLOWED_HOSTS`: Hosts permitidos (separados por coma)
- `POSTGRES_HOST`: Host de PostgreSQL
- `POSTGRES_PORT`: Puerto (default: 5432)
- `POSTGRES_DB`: Nombre de la base de datos
- `POSTGRES_USER`: Usuario de PostgreSQL
- `POSTGRES_PASSWORD`: Contraseña
