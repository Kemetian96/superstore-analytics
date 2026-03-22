# Guía de Deploy — Railway + GitHub Pages

## Paso 1 — Subir a GitHub

```bash
cd superstore-analytics

git init
git add .
git commit -m "feat: initial fullstack analytics dashboard"

# Crea el repo en github.com (sin README)
git remote add origin https://github.com/Kemetian96/superstore-analytics.git
git branch -M main
git push -u origin main
```

---

## Paso 2 — Crear proyecto en Railway

1. Ve a **railway.app** → New Project
2. Selecciona **"Deploy from GitHub repo"**
3. Conecta tu cuenta de GitHub y selecciona `superstore-analytics`
4. Railway detecta el `railway.toml` automáticamente

---

## Paso 3 — Agregar PostgreSQL en Railway

1. Dentro del proyecto en Railway → **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway crea la DB y te da las variables de entorno automáticamente

---

## Paso 4 — Configurar variables de entorno en Railway

En tu servicio de backend → **Variables** → agrega:

```
DB_HOST      = ${{Postgres.PGHOST}}
DB_PORT      = ${{Postgres.PGPORT}}
DB_NAME      = ${{Postgres.PGDATABASE}}
DB_USER      = ${{Postgres.PGUSER}}
DB_PASSWORD  = ${{Postgres.PGPASSWORD}}
```

Railway resuelve esos `${{...}}` automáticamente desde la DB que creaste.

---

## Paso 5 — Cargar el dataset en la DB de Railway

Railway te da una URL pública de conexión. Úsala así:

```bash
# En tu máquina local, con el CSV ya descargado:

# Primero obtén la URL de conexión de Railway:
# Ve a PostgreSQL → Connect → copia "Postgres Connection URL"
# Se ve así: postgresql://user:pass@host:port/railway

# Luego edita tu .env local:
DB_HOST=host-de-railway.railway.app
DB_PORT=puerto-de-railway
DB_NAME=railway
DB_USER=postgres
DB_PASSWORD=password-de-railway

# Ejecuta el script:
python scripts/load_data.py
```

Esto carga los 51K rows directamente a la DB en la nube.

---

## Paso 6 — Obtener la URL pública del backend

En Railway → tu servicio → **Settings** → **Domains** → **Generate Domain**

Te dará algo como:
```
https://superstore-analytics-production.up.railway.app
```

---

## Paso 7 — Actualizar la URL en el frontend

Edita `frontend/static/js/dashboard.js` línea 4:

```javascript
: 'https://superstore-analytics-production.up.railway.app';
```

Luego haz commit y push:

```bash
git add .
git commit -m "config: update API_BASE to Railway URL"
git push
```

---

## Paso 8 — Deploy frontend en GitHub Pages

1. Ve a tu repo en GitHub → **Settings** → **Pages**
2. Source: **"Deploy from a branch"**
3. Branch: `main` / folder: `/frontend`
4. Guarda

En 2-3 minutos tendrás:
```
https://Kemetian96.github.io/superstore-analytics
```

---

## Resultado final

```
Frontend:  https://Kemetian96.github.io/superstore-analytics
Backend:   https://superstore-analytics.up.railway.app
API Docs:  https://superstore-analytics.up.railway.app/docs
```

Tres URLs para poner en tu CV y LinkedIn.

---



## Problemas comunes    

**CORS error en el browser**
El backend ya tiene CORS abierto (`allow_origins=["*"]`), no deberías tener problemas.

**Railway pone el backend a dormir**
El plan gratuito de Railway duerme el servicio tras 30 min de inactividad. El primer request tarda ~5s en despertar. Es normal.

**CSV no carga**
Asegúrate de que el archivo se llama exactamente `Global Superstore.csv` (con espacios) o ajusta `CSV_PATH` en `.env`.
