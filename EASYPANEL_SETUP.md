# 🚀 Guía de Configuración en Easypanel

## ✅ Servicios que YA TIENES (no tocar)

- ✅ PostgreSQL (nexo_dbvector)
- ✅ Django Admin (nexo-django)

## ➕ Servicios NUEVOS a Agregar

### 1️⃣ FastAPI Backend

**Crear nuevo servicio:**

```
Nombre: dxv-api (o nexo-api)
Tipo: App
Source: GitHub
Repositorio: jvelezp13/modelodistribucion
Branch: claude/design-simple-panels-011CV13BN5D4RTTUSiVRnWaG
```

**Build Settings:**
```
Dockerfile Path: Dockerfile.api
Build Context: . (root)
```

**Environment Variables:**
```
POSTGRES_DB=nexo
POSTGRES_USER=postgres
POSTGRES_PASSWORD=[tu-password-actual]
POSTGRES_HOST=nexo_dbvector
POSTGRES_PORT=5432
DJANGO_SETTINGS_MODULE=dxv_admin.settings
```

**Network:**
```
Port: 8000 (interno)
```

**Domain:**
```
Host: api.nexo-django.vzrxex.easypanel.host
Protocol: HTTPS
Path: /
```

---

### 2️⃣ Next.js Frontend

**Crear nuevo servicio:**

```
Nombre: dxv-frontend (o nexo-dashboard)
Tipo: App
Source: GitHub
Repositorio: jvelezp13/modelodistribucion
Branch: claude/design-simple-panels-011CV13BN5D4RTTUSiVRnWaG
```

**Build Settings:**
```
Dockerfile Path: Dockerfile.frontend
Build Context: . (root)
```

**Environment Variables:**
```
NEXT_PUBLIC_API_URL=https://api.nexo-django.vzrxex.easypanel.host
```

**Network:**
```
Port: 3000 (interno)
```

**Domain:**
```
Host: dashboard.nexo-django.vzrxex.easypanel.host
Protocol: HTTPS
Path: /
```

O si prefieres usar el dominio principal:
```
Host: nexo-django.vzrxex.easypanel.host
Protocol: HTTPS
Path: /
```

---

## 🔄 Orden de Despliegue

1. ✅ **Primero: FastAPI** → Esperar que esté corriendo
2. ✅ **Segundo: Next.js** → Se conectará al API
3. ⚠️ **Opcional: Desactivar Streamlit** (si ya no lo necesitas)

---

## 🧪 Verificación

### 1. Verificar API
```
https://api.nexo-django.vzrxex.easypanel.host/
```
Debería responder:
```json
{
  "status": "ok",
  "service": "DxV Multimarcas API",
  "version": "2.0.0"
}
```

### 2. Verificar documentación automática
```
https://api.nexo-django.vzrxex.easypanel.host/docs
```
Debería mostrar la interfaz Swagger con todos los endpoints.

### 3. Verificar Frontend
```
https://dashboard.nexo-django.vzrxex.easypanel.host/
```
Debería cargar el dashboard moderno.

---

## 🐛 Troubleshooting

### Error: Frontend no encuentra package.json

**Causa:** Build Context mal configurado.

**Solución:**
- Usar `Dockerfile.frontend` (en el root)
- Build Context: `.` o `./`

### Error: Frontend no se conecta al API

**Causa:** Variable `NEXT_PUBLIC_API_URL` incorrecta.

**Solución:**
- Verificar que apunta a la URL correcta del API
- Verificar que el API esté corriendo
- Verificar que el dominio del API esté configurado

### Error: API no se conecta a la base de datos

**Causa:** Variables de conexión incorrectas.

**Solución:**
- Verificar `POSTGRES_HOST=nexo_dbvector`
- Verificar que la password sea la correcta
- Verificar que ambos servicios estén en la misma red de Easypanel

---

## 📊 Arquitectura Final

```
Usuario
  ↓
Next.js Dashboard (puerto 3000)
  ↓ HTTPS
FastAPI Backend (puerto 8000)
  ↓ TCP
Django Admin (puerto 8000) → PostgreSQL (nexo_dbvector)
  ↓
Core Simulator (Python)
```

---

## 🎯 URLs Finales

Después de configurar todo, tendrás:

- **Dashboard Moderno**: https://dashboard.nexo-django.vzrxex.easypanel.host
- **API REST**: https://api.nexo-django.vzrxex.easypanel.host
- **API Docs**: https://api.nexo-django.vzrxex.easypanel.host/docs
- **Django Admin**: https://nexo-django.vzrxex.easypanel.host/admin (sin cambios)
- **Streamlit** (opcional): https://nexo-streamlit... (si decides mantenerlo)

---

## 💡 Notas Importantes

1. **No elimines Streamlit todavía** hasta que compruebes que el nuevo dashboard funciona.
2. **Las variables de entorno** son las mismas que ya tienes en Django Admin.
3. **La base de datos** es la misma, no hay migración de datos.
4. **Django Admin sigue funcionando igual**, no lo toques.

---

## ✅ Checklist de Deployment

- [ ] Crear servicio FastAPI en Easypanel
- [ ] Configurar variables de entorno del API
- [ ] Configurar dominio del API
- [ ] Verificar que el API responde en /
- [ ] Verificar que /docs muestra Swagger
- [ ] Crear servicio Next.js Frontend
- [ ] Configurar NEXT_PUBLIC_API_URL apuntando al API
- [ ] Configurar dominio del Frontend
- [ ] Verificar que el dashboard carga
- [ ] Probar seleccionar marcas y ejecutar simulación
- [ ] (Opcional) Desactivar Streamlit
