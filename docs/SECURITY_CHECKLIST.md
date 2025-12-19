# 🔒 Checklist de Seguridad - Sistema DxV Multimarcas

**Última Actualización:** 2025-12-19
**Versión:** 1.0

---

## 📋 Pre-Despliegue a Producción

### 🔐 Variables de Entorno Críticas

**OBLIGATORIAS antes de desplegar:**

- [ ] `DJANGO_SECRET_KEY` configurado con valor único y seguro (50+ caracteres)
- [ ] `DJANGO_DEBUG=False` (o no configurado - default es False)
- [ ] `CORS_ALLOWED_ORIGINS` con dominios específicos (SIN wildcard `*`)
- [ ] `POSTGRES_PASSWORD` con contraseña fuerte (16+ caracteres, alfanumérica + símbolos)
- [ ] Todas las passwords están en variables de entorno (NO en código)
- [ ] Archivo `.env` NO está commiteado en Git (verificar `.gitignore`)

### 🛡️ Configuración Django

- [ ] `DEBUG = False` en producción (validación automática implementada)
- [ ] `ALLOWED_HOSTS` configurado con dominios específicos
- [ ] `CSRF_TRUSTED_ORIGINS` incluye solo dominios HTTPS de producción
- [ ] `SECRET_KEY` única para cada entorno (dev, staging, prod)
- [ ] Validación de SECRET_KEY habilitada (falla si es insegura en prod)

### ⚡ Configuración FastAPI

- [ ] CORS restrictivo con dominios específicos (NO `["*"]`)
- [ ] Logs muestran advertencia si CORS tiene wildcard
- [ ] HTTPS forzado en producción (configuración de proxy/load balancer)
- [ ] Logs de seguridad habilitados
- [ ] Rate limiting configurado (opcional pero recomendado)

### 💾 Base de Datos

- [ ] Usuario de BD con permisos mínimos necesarios (NO root/postgres)
- [ ] Conexión encriptada (SSL/TLS) si la BD es remota
- [ ] Backups automáticos configurados y probados
- [ ] Credentials rotadas periódicamente (cada 90 días recomendado)
- [ ] BD no expuesta públicamente (solo accesible desde app)

### 🧪 Testing de Seguridad

- [ ] Tests de CORS ejecutados y pasando
- [ ] Scan de dependencias sin vulnerabilidades críticas (`pip-audit`, `npm audit`)
- [ ] Validación de SECRET_KEY test pasa
- [ ] Endpoints públicos revisados (no exponen datos sensibles)
- [ ] Tests de autenticación/autorización pasan

### 📦 Dependencias

- [ ] `requirements.txt` actualizado sin vulnerabilidades conocidas
- [ ] `package.json` (frontend) sin vulnerabilidades críticas
- [ ] Versiones de frameworks actualizadas a releases estables

---

## 🚀 Comandos de Validación

### Validación Django

```bash
# Verificar configuración de producción
python admin_panel/manage.py check --deploy

# Debería mostrar advertencias sobre:
# - DEBUG=False
# - SECRET_KEY configurado
# - ALLOWED_HOSTS configurado
```

### Validación de Dependencias

```bash
# Python - Escanear vulnerabilidades
pip install pip-audit
pip-audit

# Node.js - Escanear vulnerabilidades
cd frontend
npm audit
npm audit fix  # Solo si es seguro
```

### Validación de Secrets

```bash
# Verificar que no hay secrets en el código
# (requiere truffleHog o git-secrets)
trufflehog git file://. --only-verified

# O manualmente:
grep -r "SECRET_KEY\|PASSWORD\|API_KEY" . --exclude-dir=node_modules --exclude-dir=.git
```

### Test de CORS

```bash
# Test manual con curl
curl -H "Origin: http://malicious-site.com" http://tu-api.com/api/marcas
# Debe fallar con CORS error

curl -H "Origin: https://tu-frontend.com" http://tu-api.com/api/marcas
# Debe funcionar correctamente
```

---

## 🔍 Verificaciones Post-Despliegue

### Inmediatamente después de desplegar:

- [ ] Endpoint de health check responde: `GET /` (API)
- [ ] Admin panel accesible y requiere login: `/admin`
- [ ] Frontend carga correctamente
- [ ] CORS permite solo orígenes configurados (probar con DevTools)
- [ ] Logs no muestran advertencias de seguridad
- [ ] Base de datos conecta correctamente
- [ ] Migraciones aplicadas: `python manage.py showmigrations`

### Primera semana:

- [ ] Monitoreo de errores configurado (Sentry, LogRocket, etc.)
- [ ] Alertas de seguridad habilitadas
- [ ] Backups verificados y restaurables
- [ ] SSL/TLS certificado válido y auto-renovable

---

## 🚨 Incidentes de Seguridad

### En caso de sospecha de vulnerabilidad:

1. **NO PÁNICO** - Evaluar la situación
2. **Documentar** - Capturar evidencia (logs, requests)
3. **Contener** - Si es activo, bloquear IP/usuario
4. **Notificar** - Contactar al equipo de seguridad
5. **Remediar** - Aplicar fix y desplegar
6. **Post-mortem** - Documentar lección aprendida

### Contactos de Emergencia:

- **Email:** seguridad@tuempresa.com
- **Slack:** #security-incidents
- **On-call:** [Número de teléfono]

---

## 📊 Niveles de Severidad

| Nivel | Descripción | Tiempo de Respuesta |
|-------|-------------|-------------------|
| 🔴 **CRÍTICO** | Vulnerabilidad activa explotable | < 4 horas |
| 🟠 **ALTO** | Vulnerabilidad potencial con alto impacto | < 24 horas |
| 🟡 **MEDIO** | Vulnerabilidad con impacto limitado | < 1 semana |
| 🟢 **BAJO** | Best practice no seguida | < 1 mes |

---

## 🔄 Mantenimiento de Seguridad

### Mensual:

- [ ] Revisar logs de acceso anormal
- [ ] Ejecutar `pip-audit` y `npm audit`
- [ ] Verificar que backups están funcionando
- [ ] Revisar usuarios con acceso privilegiado

### Trimestral:

- [ ] Rotar credenciales de BD
- [ ] Actualizar dependencias a versiones estables
- [ ] Revisar políticas de CORS y ALLOWED_HOSTS
- [ ] Audit completo de seguridad

### Anual:

- [ ] Penetration testing externo (opcional)
- [ ] Revisar y actualizar políticas de seguridad
- [ ] Training de seguridad para el equipo

---

## 📚 Recursos Adicionales

### Documentación Oficial:

- [Django Security Best Practices](https://docs.djangoproject.com/en/stable/topics/security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Herramientas Recomendadas:

- **Scanners:** `pip-audit`, `safety`, `bandit` (Python)
- **Secrets:** `truffleHog`, `git-secrets`
- **Monitoring:** Sentry, LogRocket, DataDog
- **SSL:** Let's Encrypt (gratuito), Cloudflare

---

## ✅ Checklist Rápido (1 Minuto)

**Antes de cada deploy a producción:**

```bash
# 1. Verificar que DEBUG está False
grep "DEBUG = False" admin_panel/dxv_admin/settings.py

# 2. Verificar que CORS no tiene wildcard en código
grep -n "allow_origins.*\*" api/main.py
# No debe retornar resultados

# 3. Ejecutar tests de seguridad
pytest tests/test_security.py -v

# 4. Verificar Django deployment checklist
python admin_panel/manage.py check --deploy

# 5. Si todo OK:
git tag -a v1.0.0 -m "Release 1.0.0 - Security validated"
git push origin v1.0.0
```

---

**Versión del Checklist:** 1.0
**Próxima Revisión:** 2026-01-19

Este checklist debe actualizarse cuando:
- Se agreguen nuevas funcionalidades de seguridad
- Se descubran nuevas vulnerabilidades
- Cambien las mejores prácticas de la industria
