# Rodeo de Cría — App de gestión

App web mobile-first para gestión de rodeo de cría vacuno.
Base de datos con 439 vacas y 3 temporadas históricas ya cargadas.

## Deploy en Railway (5 minutos)

1. Creá una cuenta en https://railway.app (gratis)
2. Nuevo proyecto → "Deploy from GitHub repo"
3. Subí esta carpeta a un repo de GitHub
4. Railway detecta el Procfile automáticamente
5. Agregá variable de entorno: SECRET_KEY = (cualquier texto largo)
6. ¡Listo! Railway te da una URL pública

## Correr localmente

```bash
pip install flask
python app.py
# Abrir http://localhost:5000
```

## Funcionalidades

- 🐮 Registrar partos desde el celular en el campo
- 🔍 Buscar vacas por caravana con historial completo
- 📋 Cargar eventos reproductivos (DAO, IATF, diagnóstico, eco)
- 📊 Dashboard: % preñez por toro, GMD, candidatas a baja
- ➕ Dar de alta vacas nuevas

## Estructura

- `app.py` — Backend Flask con todas las rutas
- `database.py` — Modelos y conexión SQLite
- `rodeo.db` — Base de datos con datos históricos
- `templates/` — Vistas HTML mobile-first
