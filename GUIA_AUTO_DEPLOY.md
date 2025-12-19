# 🚀 Guía de Auto-Deploy con EasyPanel

**Fecha:** 19 de Diciembre, 2025
**Objetivo:** Eliminar despliegues manuales usando la integración nativa de GitHub con EasyPanel
**Tiempo de configuración:** ~15 minutos
**Complejidad:** Muy Baja ✅

---

## 📊 Resumen Ejecutivo (Para No Técnicos)

### ¿Qué vamos a lograr?

**ANTES (Manual - Actual):**
```
Tú escribes código
  ↓
git push
  ↓
Abres EasyPanel manualmente
  ↓
Haces clic en "Deploy"
  ↓
Esperas que termine
```

**DESPUÉS (Automático):**
```
Tú escribes código
  ↓
git push
  ↓
¡LISTO! EasyPanel se encarga del resto automáticamente
```

### ¿Cómo funciona?

Es como tener un asistente que constantemente vigila tu GitHub y dice:

> "¿Hubo cambios nuevos? Déjame desplegarlos automáticamente por ti."

**Ventajas:**
- ✅ **Ahorro de tiempo:** De 5 minutos por deploy → 10 segundos (solo git push)
- ✅ **Menos errores:** No olvidas desplegar cambios
- ✅ **Más productivo:** Te enfocas en programar, no en hacer clic en botones
- ✅ **Cero costo:** Gratis, usa funcionalidad nativa de EasyPanel
- ✅ **Cero mantenimiento:** Una vez configurado, funciona para siempre

---

## 🎯 Arquitectura de Despliegue

Tu aplicación tiene **3 servicios independientes** que necesitan auto-deploy:

| Servicio | Dockerfile | Puerto | Rama GitHub |
|----------|-----------|--------|-------------|
| **Frontend** (Next.js) | `frontend/Dockerfile` | 3000 | `main` |
| **API** (FastAPI) | `Dockerfile.api` | 8000 | `main` |
| **Admin Panel** (Django) | `admin_panel/Dockerfile` | 8000 | `main` |

Cada servicio se desplegará **automáticamente** cuando hagas push a GitHub.

---

## 📝 Paso 1: Crear GitHub Token (5 minutos)

### ¿Qué es un GitHub Token?

Es como una "llave" que le das a EasyPanel para que pueda:
- **Leer** tu código cuando hay cambios
- **Recibir notificaciones** cuando haces push
- **Desplegar** automáticamente

### Instrucciones:

1. **Ve a GitHub:**
   - URL directa: https://github.com/settings/tokens?type=beta
   - O manualmente: GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens

2. **Clic en "Generate new token"**

3. **Configuración del Token:**

   **Token name:**
   ```
   EasyPanel-AutoDeploy-ModeloDistribucion
   ```

   **Expiration:**
   - Recomendado: **1 año** (más seguro)
   - Alternativa: **No expiration** (más conveniente)

   **Repository access:**
   - Selecciona: **"Only select repositories"**
   - Elige: `jvelezp13/modelodistribucion` (o el nombre de tu repo)

   **Permissions (Permisos):**

   | Permission | Access Level | ¿Por qué? |
   |-----------|-------------|-----------|
   | **Contents** | Read-only | Para leer el código |
   | **Metadata** | Read-only | Requerido por GitHub |
   | **Webhooks** | Read and write | **CRÍTICO** para auto-deploy |

   > ⚠️ **IMPORTANTE:** Si no das permiso de "Webhooks - Read and write", el auto-deploy NO funcionará.

4. **Generate token**

5. **COPIAR Y GUARDAR el token:**
   - Aparecerá algo como: `github_pat_11A...XYZ123`
   - **Cópialo AHORA** - Solo lo verás una vez
   - Guárdalo temporalmente en un lugar seguro (eliminarás después de configurar EasyPanel)

---

## 🔧 Paso 2: Configurar Auto-Deploy en EasyPanel (10 minutos)

Vas a hacer esto **3 veces** (una por servicio: Frontend, API, Admin Panel).

### Configuración por Servicio:

#### A. Frontend (Next.js)

1. **Ve a EasyPanel** → Tu proyecto → Servicio de **Frontend**

2. **Ir a Settings:**
   - Busca la pestaña o sección "Settings"
   - O directamente: "GitHub" o "Code Source"

3. **Pegar GitHub Token:**
   - Campo: "GitHub Token" o "Personal Access Token"
   - Pega el token que copiaste: `github_pat_11A...`
   - Clic en **"Save"** o **"Update"**
   - Verás: ✅ **"GitHub token updated"**

4. **Habilitar Auto-Deploy:**
   - Busca el botón o toggle: **"Auto Deploy"** o **"Enable Webhooks"**
   - **Actívalo** (ON)
   - EasyPanel dirá algo como: "Webhook configured in GitHub repository"

5. **Verificar configuración:**
   - Deberías ver:
     - ✅ GitHub conectado
     - ✅ Auto-deploy habilitado
     - ✅ Branch: `main` (o la rama que uses)

#### B. API (FastAPI)

1. Repite **exactamente los mismos pasos** del Frontend
2. Pero en el servicio de **API**
3. Usa el **mismo token** de GitHub

#### C. Admin Panel (Django)

1. Repite los mismos pasos
2. En el servicio de **Admin Panel**
3. Usa el **mismo token** de GitHub

---

## ✅ Paso 3: Verificar que Funciona (5 minutos)

### Test 1: Cambio Simple en Frontend

1. **Edita un archivo del frontend:**
   ```bash
   # Abre cualquier archivo, por ejemplo:
   nano frontend/src/app/page.tsx

   # Agrega un comentario:
   // Test auto-deploy - 2025-12-19
   ```

2. **Commit y Push:**
   ```bash
   git add frontend/
   git commit -m "test: verificar auto-deploy en frontend"
   git push origin main
   ```

3. **Observa EasyPanel:**
   - Ve a EasyPanel → Frontend
   - Deberías ver **automáticamente**:
     - 🟡 "Deploying..." o "Building..."
     - Logs mostrando el build
     - 🟢 "Deployed successfully" (después de 2-5 minutos)

4. **Verifica la app:**
   - Abre tu frontend en el navegador
   - Debería funcionar normalmente

### Test 2: Cambio en API

```bash
# Edita api/main.py (agrega un comentario)
git add api/
git commit -m "test: verificar auto-deploy en API"
git push origin main
```

Observa EasyPanel → API → Debería desplegar automáticamente.

### Test 3: Cambio en Admin Panel

```bash
# Edita algún archivo de admin_panel
git add admin_panel/
git commit -m "test: verificar auto-deploy en admin panel"
git push origin main
```

Observa EasyPanel → Admin Panel → Deployment automático.

---

## 🎓 Cómo Usar Auto-Deploy en el Día a Día

### Flujo de Trabajo Normal:

```bash
# 1. Haces cambios en tu código
# (Editas archivos, agregas features, fixes, etc.)

# 2. Commit localmente
git add .
git commit -m "feat: nueva funcionalidad X"

# 3. Push a GitHub
git push origin main

# 4. ¡LISTO!
# EasyPanel se encarga del resto automáticamente
# Recibe notificación → Descarga código → Build → Deploy
```

### ¿Qué pasa si hay un error?

**Escenario:** Haces push de código con un bug.

**Antes (Manual):**
- Tenías que hacer deploy manual
- Si fallaba, tenías que revisar logs manualmente
- Hacer fix y volver a desplegar manualmente

**Ahora (Auto-Deploy):**
1. **Push con bug:**
   ```bash
   git push origin main
   ```

2. **EasyPanel intenta desplegar:**
   - Ve a EasyPanel → Logs
   - Verás el error exacto
   - El deploy **falla** (la versión anterior sigue funcionando)

3. **Fix rápido:**
   ```bash
   # Corriges el bug
   git add .
   git commit -m "fix: corregir error X"
   git push origin main
   ```

4. **Auto-Deploy vuelve a intentar:**
   - Ahora con el código corregido
   - Build exitoso ✅
   - Deploy exitoso ✅

### Consejos Pro:

1. **Commits Pequeños y Frecuentes:**
   ```bash
   # ✅ BIEN - Fácil de revertir
   git commit -m "fix: corregir validación de email"
   git push

   # ❌ MALO - Si falla, no sabes qué causó el error
   git commit -m "cambios varios"
   git push
   ```

2. **Mensajes de Commit Descriptivos:**
   ```bash
   # ✅ BIEN - Sabes exactamente qué se desplegó
   git commit -m "feat: agregar filtro de marcas en dashboard"

   # ❌ MALO - No sabes qué cambió
   git commit -m "update"
   ```

3. **Revisar Logs Después de Push:**
   - Después de hacer `git push`
   - Ve a EasyPanel rápidamente
   - Verifica que el deployment empezó
   - Si hay error, actúa rápido

---

## 🛡️ Seguridad y Mejores Prácticas

### 1. Protección del Token de GitHub

**NUNCA:**
- ❌ Commitear el token en tu código
- ❌ Compartir el token públicamente
- ❌ Dejar el token en archivos de texto

**SIEMPRE:**
- ✅ Guardar solo en EasyPanel (Settings)
- ✅ Usar tokens con permisos mínimos necesarios
- ✅ Rotar tokens cada 6-12 meses

### 2. Proteger la Rama Main (Opcional)

Si quieres más control antes de auto-deploy:

1. **Ve a GitHub:** Settings → Branches
2. **Add branch protection rule:**
   - Branch name pattern: `main`
   - ✅ Require pull request reviews before merging
   - ✅ Require status checks to pass (cuando tengas tests)

**Ventaja:**
- Cambios solo se despliegan si pasan revisión
- Reduces errores en producción

**Desventaja:**
- Más pasos (crear PR, aprobar, merge)
- Para trabajar solo, puede ser innecesario

### 3. Variables de Entorno Críticas

**NUNCA las cambies en .env y las commitees:**
```bash
# ❌ MALO - Nunca hacer esto
echo "DJANGO_SECRET_KEY=abc123" >> .env
git add .env
git commit -m "update secret"
```

**SIEMPRE configura en EasyPanel:**
- Ve a EasyPanel → Service → Environment Variables
- Edita ahí directamente
- EasyPanel las mantendrá seguras

---

## 🔍 Monitoreo y Troubleshooting

### Verificar Estado del Deployment

**En EasyPanel:**
1. Ve a tu proyecto
2. Cada servicio mostrará:
   - 🟢 **Running** - Todo bien
   - 🟡 **Deploying** - Desplegando ahora
   - 🔴 **Failed** - Hubo error

### Revisar Logs

**Ver logs en tiempo real:**
1. EasyPanel → Servicio → Logs
2. Filtra por:
   - Build logs (errores de construcción)
   - Runtime logs (errores al correr)

### Errores Comunes

#### Error 1: "Webhook failed to configure"

**Causa:** Token de GitHub sin permisos de Webhooks

**Solución:**
1. Genera nuevo token con permiso "Webhooks - Read and write"
2. Re-configura en EasyPanel
3. Vuelve a habilitar Auto Deploy

#### Error 2: "Build failed - Dockerfile not found"

**Causa:** EasyPanel no encuentra el Dockerfile correcto

**Solución:**
1. Verifica en EasyPanel → Settings:
   - Build Path: Debe ser correcto (`frontend/`, `admin_panel/`, o root)
   - Dockerfile: Ruta correcta (`Dockerfile`, `Dockerfile.api`, etc.)

#### Error 3: "Container crashed after deployment"

**Causa:** Error en el código o configuración incorrecta

**Solución:**
1. Revisa logs: EasyPanel → Logs
2. Busca el error específico
3. Haz fix en local
4. Push nuevamente (auto-deploy volverá a intentar)

#### Error 4: "Environment variables not found"

**Causa:** Variables de entorno no configuradas en EasyPanel

**Solución:**
1. Ve a EasyPanel → Service → Environment
2. Agrega las variables necesarias:
   - `DJANGO_SECRET_KEY`
   - `POSTGRES_HOST`
   - `NEXT_PUBLIC_API_URL`
   - etc.

---

## 📊 Comparación: Antes vs. Después

### Tiempo de Deployment

| Actividad | Antes (Manual) | Después (Auto) | Ahorro |
|-----------|---------------|----------------|--------|
| **Código + Commit** | 10 min | 10 min | - |
| **Push a GitHub** | 30 seg | 30 seg | - |
| **Ir a EasyPanel** | 1 min | - | 1 min ✅ |
| **Hacer Deploy Manual** | 30 seg × 3 servicios | - | 1.5 min ✅ |
| **Esperar Deploy** | 5 min | 5 min (automático) | - |
| **Verificar** | 2 min | 2 min | - |
| **TOTAL** | **~19 min** | **~17.5 min** | **1.5 min por deploy** |

Pero el **ahorro real** es:
- ✅ **Mental:** No tienes que recordar hacer deploy manual
- ✅ **Contexto:** No cambias de ventana (GitHub ↔ EasyPanel)
- ✅ **Errores:** No olvidas desplegar algún servicio
- ✅ **Productividad:** Haces push y sigues trabajando en otra cosa

### Productividad

**Con 10 deployments por semana:**
- Antes: 19 min × 10 = **190 minutos (3.2 horas)**
- Después: 12.5 min × 10 = **125 minutos (2.1 horas)**
- **Ahorro: 65 minutos por semana** = **1 hora extra para programar** ✅

---

## 🚀 Próximos Pasos (Opcional)

Una vez que tengas auto-deploy funcionando, puedes mejorar aún más:

### 1. Agregar Tests Automáticos (Sprint 3)

**Qué harías:**
- Agregar tests con pytest (API, Django)
- Configurar GitHub Actions para correr tests ANTES de que EasyPanel despliegue

**Ventaja:**
- Si los tests fallan, el código malo nunca llega a producción
- Auto-deploy solo pasa si tests ✅

**Cuándo hacerlo:**
- Después de completar Sprint 3 (Testing y Performance)

### 2. Estrategia de Branches

**Opción A: Branch Único (Actual - Recomendado para ti)**
```
main → Auto-deploy a producción
```
- Más simple
- Perfecto para trabajar solo con AI
- Deploy inmediato

**Opción B: Múltiples Branches (Para equipos)**
```
dev → Testing manual
staging → Pre-producción (auto-deploy a servidor de staging)
main → Producción (auto-deploy solo si staging OK)
```

### 3. Rollback Automático

EasyPanel permite hacer rollback si algo sale mal:

1. Ve a EasyPanel → Service → Deployments
2. Verás lista de deployments anteriores
3. Clic en "Redeploy" en una versión anterior
4. Rollback instantáneo ✅

---

## 🎯 Checklist Final

Antes de considerar configuración completa:

### Configuración Inicial:
- [ ] GitHub token creado con permisos correctos
- [ ] Token configurado en EasyPanel (Frontend)
- [ ] Token configurado en EasyPanel (API)
- [ ] Token configurado en EasyPanel (Admin Panel)
- [ ] Auto-deploy habilitado en los 3 servicios

### Verificación:
- [ ] Test push en Frontend → Deployment automático ✅
- [ ] Test push en API → Deployment automático ✅
- [ ] Test push en Admin Panel → Deployment automático ✅
- [ ] Logs sin errores
- [ ] Aplicación funciona correctamente después de auto-deploy

### Documentación:
- [ ] Guardar esta guía para referencia futura
- [ ] Actualizar `GUIA_DESPLIEGUE.md` si es necesario
- [ ] Documentar variables de entorno en EasyPanel

### Seguridad:
- [ ] Token de GitHub no commiteado en código
- [ ] `.env` en `.gitignore`
- [ ] Variables sensibles solo en EasyPanel

---

## 📚 Recursos Adicionales

### Documentación Oficial:
- [EasyPanel - GitHub Integration](https://easypanel.io/docs/code-sources/github)
- [EasyPanel - App Service](https://easypanel.io/docs/services/app)
- [GitHub - Fine-grained Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-fine-grained-personal-access-token)

### Soporte:
- **EasyPanel Docs:** https://easypanel.io/docs
- **GitHub Discussions:** https://github.com/easypanel-io/easypanel/discussions
- **Tu GUIA_DESPLIEGUE.md:** Para configuración específica de tu proyecto

---

## 💡 Conclusión

### ¿Qué logramos?

✅ **Eliminado:** Proceso manual de deployment
✅ **Automatizado:** Push → Auto-deploy
✅ **Simplificado:** Cero configuración compleja (sin GitHub Actions)
✅ **Optimizado:** Usa la mejor opción para tu stack

### ¿Por qué esta es la mejor solución?

**Comparado con GitHub Actions:**
- ✅ Más simple (5 min vs. horas)
- ✅ Cero mantenimiento (vs. mantener `.yml` files)
- ✅ Integración nativa con EasyPanel
- ✅ Mismo resultado final

**Comparado con Manual:**
- ✅ Ahorra tiempo (1+ hora por semana)
- ✅ Menos errores (no olvidas desplegar)
- ✅ Más productivo (te enfocas en código)

### Siguiente Nivel (Futuro)

Cuando completes Sprint 3 (Testing), podrás:
- Agregar tests automáticos pre-deployment
- GitHub Actions solo para correr tests
- Auto-deploy solo si tests pasan
- Sistema de producción de nivel enterprise ✅

**Pero por ahora:** Auto-deploy simple y funcional es PERFECTO para tu caso.

---

**Preparado por:** Claude Code
**Fecha:** 2025-12-19
**Versión:** 1.0
**Próxima Revisión:** Cuando implementes Sprint 3 (Tests)

---

## 🆘 ¿Necesitas Ayuda?

Si tienes problemas:

1. **Revisa esta guía** - Sección "Troubleshooting"
2. **Verifica logs** - EasyPanel → Logs
3. **Consulta docs oficiales** - Links arriba
4. **Pregúntame** - Estoy aquí para ayudar

¡Éxito con tu auto-deploy! 🚀
