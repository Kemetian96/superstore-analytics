# 📊 Global Superstore Analytics Dashboard

> Dashboard analítico fullstack construido con FastAPI, PostgreSQL y Chart.js  
> Dataset: [Kaggle Global Superstore](https://www.kaggle.com/datasets/apoorvaappz/global-super-store-dataset) — más de 51,000 filas

**[🔴 Live Demo](https://kemetian96.github.io/superstore-analytics/frontend/)** · **[API Docs](https://superstore-analytics.up.railway.app/docs)**

---

## Capturas de pantalla

> *(agrega capturas aquí una vez desplegado)*

---

## Stack tecnológico

| Capa      | Tecnología          | Por qué                                  |
|-----------|---------------------|------------------------------------------|
| Backend   | FastAPI (Python)    | Moderno, rápido y con documentación Swagger autogenerada |
| Base de datos | PostgreSQL      | Base de datos relacional real con consultas analíticas |
| Frontend  | HTML + Chart.js     | Sin sobrecarga de frameworks, DOM puro   |
| Despliegue| Railway             | Plan gratuito con PostgreSQL incluido    |
| Dataset   | Kaggle (CSV → SQL)  | Pipeline de ingeniería de datos con información real |

---

## Funcionalidades

- **6 KPIs** — ventas, ganancia, margen, pedidos, descuento y total de filas
- **5 gráficos interactivos** — línea, barras, dona, área polar y gráfico combinado
- **Filtros dinámicos** — año, categoría, región, segmento y mercado
- **Tabla de datos paginada** — más de 51 mil pedidos navegables
- **API REST** con documentación completa en Swagger en `/docs`
- **Pipeline de datos** — CSV → limpieza con pandas → inserción masiva en PostgreSQL

---

## Arquitectura

```
Kaggle CSV
    ↓
scripts/load_data.py  (limpieza con pandas + inserción masiva)
    ↓
PostgreSQL (Railway)
    ↓
Backend FastAPI  ← /api/kpis, /api/sales-by-month, etc.
    ↓
Frontend con Chart.js (GitHub Pages)
```

---

## Endpoints de la API

| Método | Endpoint               | Descripción                        |
|--------|------------------------|------------------------------------|
| GET    | `/api/filters`         | Valores disponibles para los filtros |
| GET    | `/api/kpis`            | KPIs principales con filtros dinámicos |
| GET    | `/api/sales-by-month`  | Serie temporal mensual             |
| GET    | `/api/sales-by-category` | Desglose por categoría y subcategoría |
| GET    | `/api/sales-by-region` | Rendimiento por región             |
| GET    | `/api/yearly-trend`    | Comparativa interanual con % de margen |
| GET    | `/api/sales-by-segment`| Distribución por segmento de cliente |
| GET    | `/api/top-countries`   | Top N países por ingresos          |
| GET    | `/api/orders`          | Tabla paginada con detalle de pedidos |
| GET    | `/api/health`          | Verificación de estado + total de filas |

Todos los endpoints aceptan parámetros opcionales: `year`, `category`, `region`, `segment`, `market`

---

## Ejecución local

**1. Clonar e instalar**
```bash
git clone https://github.com/Kemetian96/superstore-analytics
cd superstore-analytics
pip install -r requirements.txt
```

**2. Configurar la base de datos**
```bash
# Crear la base de datos en PostgreSQL
createdb superstore

# Copiar el archivo de entorno y configurarlo
cp .env.example .env
# Editar `.env` con tus credenciales de base de datos
```

**3. Cargar el dataset**
```bash
# Colocar "Global Superstore.csv" en la raíz del proyecto
python scripts/load_data.py
```

**4. Iniciar el backend**
```bash
uvicorn backend.main:app --reload
# API disponible en http://localhost:8000
# Documentación en http://localhost:8000/docs
```

**5. Abrir el frontend**
```bash
# Abrir `frontend/index.html` en el navegador
# O levantar un servidor simple:
cd frontend && python -m http.server 3000
```

---

## Despliegue

Consulta [DEPLOY.md](DEPLOY.md) para ver las instrucciones paso a paso de despliegue en Railway + GitHub Pages.

---

## Notas de ingeniería de datos

El pipeline de `scripts/load_data.py`:
- Lee el CSV original con codificación latin-1
- Normaliza los nombres de columnas a `snake_case`
- Interpreta fechas con formato `dayfirst`
- Convierte campos numéricos y rellena `NaN` con 0
- Elimina filas sin `order_date`
- Inserta datos masivamente con `execute_values` (1000 filas por lote)
- Crea índices sobre fecha, categoría, región, segmento y país

---

## Licencia

MIT
