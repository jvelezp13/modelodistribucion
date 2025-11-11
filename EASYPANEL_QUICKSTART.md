# 🚀 Guía Rápida - Deploy en Easypanel

## ✅ Pre-requisitos Completados

- [x] PostgreSQL: `nexo_dbvector` (base de datos: `nexo`)
- [x] Credenciales configuradas
- [x] Modelos Django con prefijo `dxv_`

---

## 📋 Pasos para Deploy

### **1. Crear App Django en Easypanel**

1. En Easypanel: **Apps** → **Create App**
2. Selecciona: **From Git Repository**
3. Configuración:
   - **Repository URL**: `https://github.com/jvelezp13/modelodistribucion`
   - **Branch**: `claude/design-simple-panels-011CV13BN5D4RTTUSiVRnWaG`
   - **Build Method**: `Dockerfile`
   - **Dockerfile Path**: `admin_panel/Dockerfile`
   - **Build Context**: `/` (raíz del repo)
   - **Port**: `8000`

4. **Variables de Entorno**:
   ```
   DJANGO_SECRET_KEY=cambia-esto-por-una-clave-super-larga-y-segura-usa-generador
   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=*
   POSTGRES_DB=nexo
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=d5f50a865cc2d06812ba
   POSTGRES_HOST=nexo_dbvector
   POSTGRES_PORT=5432
   ```

5. Click **Deploy**

---

### **2. Esperar que el Deploy Complete**

Verás el progreso del build en Easypanel. Espera a que diga:
```
✅ Deployment successful
```

---

### **3. Crear las Tablas (Migraciones)**

Una vez desplegado:

1. En Easypanel, abre la **Terminal/Console** de tu app Django
2. Ejecuta estos comandos en orden:

```bash
# Crear las migraciones
python manage.py makemigrations

# Aplicar migraciones (esto crea las tablas con prefijo dxv_)
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser
```

Te pedirá:
- **Username**: (tu nombre de usuario)
- **Email**: tu-email@ejemplo.com
- **Password**: (elige una segura)
- **Confirmar password**

---

### **4. Importar Datos desde YAML (Opcional)**

Si quieres importar Nutresa y datos de ejemplo:

```bash
python manage.py import_from_yaml --data-path=../data --config-path=../config
```

Verás:
```
✓ Parámetros 2025 creados
✓ Factor comercial creado
✓ Marca Nutresa creada
✓ 7 registros de personal comercial importados
...
✅ Importación completada exitosamente
```

---

### **5. Acceder al Panel Admin**

Ya puedes acceder a:
```
https://tu-app-django.easypanel.host/admin/
```

Login con el superusuario que creaste.

---

### **6. Verificar Tablas en pgweb**

Abre pgweb desde tu servicio PostgreSQL y ejecuta:

```sql
-- Ver todas las tablas del proyecto
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'dxv_%';
```

Deberías ver:
```
dxv_marca
dxv_personal_comercial
dxv_personal_logistico
dxv_vehiculo
dxv_proyeccion_ventas
dxv_volumen_operacion
dxv_parametros_macro
dxv_factor_prestacional
dxv_personal_administrativo
dxv_gasto_administrativo
dxv_gasto_comercial
dxv_gasto_logistico
dxv_impuesto
```

---

## 🎯 ¡Listo!

Ya tienes:
- ✅ PostgreSQL con base "nexo"
- ✅ 13 tablas creadas con prefijo `dxv_`
- ✅ Panel Admin funcionando
- ✅ Datos importados (si lo ejecutaste)

---

## 🔧 Solución de Problemas

### Error: "relation does not exist"
**Solución**: No corriste las migraciones. Ejecuta:
```bash
python manage.py migrate
```

### Error: "password authentication failed"
**Solución**: Verifica las credenciales en las variables de entorno.

### No puedo acceder al admin
**Solución**: Verifica que `DJANGO_ALLOWED_HOSTS=*` esté configurado.

---

## 📊 Próximos Pasos

1. **Agregar datos** desde el Panel Admin
2. **Deploy Streamlit Dashboard** (opcional, para visualización)
3. **Configurar dominio personalizado** en Easypanel
