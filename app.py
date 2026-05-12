from flask import Flask, render_template, request, jsonify, redirect, url_for
from database import init_db, get_db
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'rodeo-secret-2024')

# Inicializar DB y cargar datos históricos al arrancar
with app.app_context():
    init_db()
    try:
        from seed_render import seed_if_empty
        seed_if_empty()
    except Exception as e:
        print(f"Seed omitido: {e}")

@app.before_request
def setup():
    init_db()

# ─── INICIO ───────────────────────────────────────────────
@app.route('/')
def index():
    db = get_db()
    stats = {
        'vacas':    db.execute("SELECT COUNT(*) FROM vacas WHERE estado='Activa'").fetchone()[0],
        'toros':    db.execute("SELECT COUNT(*) FROM toros WHERE aptitud='APTO' OR aptitud IS NULL").fetchone()[0],
        'terneros': db.execute("SELECT COUNT(*) FROM terneros").fetchone()[0],
        'eventos':  db.execute("SELECT COUNT(DISTINCT temporada) FROM eventos").fetchone()[0],
    }
    temporadas = db.execute("SELECT DISTINCT temporada FROM eventos ORDER BY temporada DESC").fetchall()
    db.close()
    return render_template('index.html', stats=stats, temporadas=[r['temporada'] for r in temporadas])

# ─── BUSCAR VACA ──────────────────────────────────────────
@app.route('/buscar')
def buscar():
    q = request.args.get('q','').strip()
    if not q:
        return render_template('buscar.html', resultados=[], q='')
    db = get_db()
    resultados = db.execute(
        "SELECT * FROM vacas WHERE ide LIKE ? OR ide LIKE ? ORDER BY ide LIMIT 20",
        (f'%{q}%', f'%{q.replace(" ","")}%')
    ).fetchall()
    db.close()
    return render_template('buscar.html', resultados=resultados, q=q)

# ─── FICHA DE VACA ───────────────────────────────────────
@app.route('/vaca/<ide>')
def ficha_vaca(ide):
    db = get_db()
    vaca = db.execute("SELECT * FROM vacas WHERE ide=?", (ide,)).fetchone()
    if not vaca:
        db.close()
        return render_template('error.html', msg=f'Vaca {ide} no encontrada.'), 404
    eventos = db.execute(
        "SELECT * FROM eventos WHERE ide_vaca=? ORDER BY temporada DESC", (ide,)
    ).fetchall()
    terneros = db.execute(
        "SELECT * FROM terneros WHERE ide_madre=? ORDER BY temporada DESC", (ide,)
    ).fetchall()
    madre = None
    if vaca['ide_madre']:
        madre = db.execute("SELECT * FROM vacas WHERE ide=?", (vaca['ide_madre'],)).fetchone()
    hijos = db.execute("SELECT * FROM vacas WHERE ide_madre=?", (ide,)).fetchall()
    db.close()
    return render_template('ficha_vaca.html', vaca=vaca, eventos=eventos,
                           terneros=terneros, madre=madre, hijos=hijos)

# ─── REGISTRAR NACIMIENTO (campo) ────────────────────────
@app.route('/nacimiento', methods=['GET','POST'])
def nacimiento():
    db = get_db()
    if request.method == 'POST':
        data = request.form
        ide_madre = data.get('ide_madre','').strip().replace(' ','')
        caravana  = data.get('caravana','').strip()
        sexo      = data.get('sexo','').strip()
        potrero   = data.get('potrero','').strip()
        semana    = data.get('semana','').strip()
        raza      = data.get('raza','').strip()
        temporada = int(data.get('temporada', 2025))

        vaca = db.execute("SELECT ide FROM vacas WHERE ide=?", (ide_madre,)).fetchone()
        if not vaca:
            db.close()
            return jsonify({'ok': False, 'error': f'Vaca {ide_madre} no encontrada en el sistema.'})

        ya_existe = db.execute(
            "SELECT id FROM terneros WHERE caravana=? AND temporada=?", (caravana, temporada)
        ).fetchone()
        if ya_existe:
            db.close()
            return jsonify({'ok': False, 'error': f'Caravana {caravana} ya registrada en temporada {temporada}.'})

        db.execute('''INSERT INTO terneros (caravana, ide_madre, temporada, sexo, raza, semana_nacimiento, potrero)
                      VALUES (?,?,?,?,?,?,?)''',
                   (caravana, ide_madre, temporada, sexo, raza, semana, potrero))
        db.execute('''UPDATE eventos SET caravana_ternero=?
                      WHERE ide_vaca=? AND temporada=? AND (caravana_ternero IS NULL OR caravana_ternero='')''',
                   (caravana, ide_madre, temporada))
        db.commit()
        db.close()
        return jsonify({'ok': True, 'msg': f'✓ Ternero {caravana} registrado. Madre: {ide_madre}'})

    potreros = ['T','N','M','F1','F2','R','RUTA','LP']
    razas = ['AA','RA','HA','HE']
    db.close()
    return render_template('nacimiento.html', potreros=potreros, razas=razas)

# ─── NUEVA TEMPORADA / EVENTO ─────────────────────────────
@app.route('/evento/nuevo', methods=['GET','POST'])
def nuevo_evento():
    db = get_db()
    if request.method == 'POST':
        data = request.form
        ide = data.get('ide_vaca','').strip().replace(' ','')
        temporada = int(data.get('temporada', 2025))

        vaca = db.execute("SELECT ide FROM vacas WHERE ide=?", (ide,)).fetchone()
        if not vaca:
            db.close()
            return jsonify({'ok': False, 'error': f'Vaca {ide} no encontrada.'})

        existe = db.execute(
            "SELECT id FROM eventos WHERE ide_vaca=? AND temporada=?", (ide, temporada)
        ).fetchone()
        if existe:
            db.execute('''UPDATE eventos SET dao_sincro=?,toro_iatf=?,diagnostico_iatf=?,
                          ecografia_final=?,toro_entore=?,eco_entore=?,observaciones=?
                          WHERE ide_vaca=? AND temporada=?''',
                       (data.get('dao_sincro') or None, data.get('toro_iatf') or None,
                        data.get('diagnostico_iatf') or None, data.get('ecografia_final') or None,
                        data.get('toro_entore') or None, data.get('eco_entore') or None,
                        data.get('observaciones') or None, ide, temporada))
        else:
            db.execute('''INSERT INTO eventos (ide_vaca,temporada,dao_sincro,toro_iatf,diagnostico_iatf,
                          ecografia_final,toro_entore,eco_entore,observaciones)
                          VALUES (?,?,?,?,?,?,?,?,?)''',
                       (ide, temporada, data.get('dao_sincro') or None, data.get('toro_iatf') or None,
                        data.get('diagnostico_iatf') or None, data.get('ecografia_final') or None,
                        data.get('toro_entore') or None, data.get('eco_entore') or None,
                        data.get('observaciones') or None))
        db.commit()
        db.close()
        return jsonify({'ok': True, 'msg': f'✓ Evento {temporada} guardado para vaca {ide}'})

    toros = db.execute("SELECT * FROM toros ORDER BY idv").fetchall()
    db.close()
    return render_template('nuevo_evento.html', toros=toros)

# ─── NUEVA VACA ───────────────────────────────────────────
@app.route('/vaca/nueva', methods=['GET','POST'])
def nueva_vaca():
    db = get_db()
    if request.method == 'POST':
        data = request.form
        ide = data.get('ide','').strip().replace(' ','')
        if not ide:
            db.close()
            return jsonify({'ok': False, 'error': 'IDE requerido.'})
        existe = db.execute("SELECT id FROM vacas WHERE ide=?", (ide,)).fetchone()
        if existe:
            db.close()
            return jsonify({'ok': False, 'error': f'Vaca {ide} ya existe.'})
        db.execute('''INSERT INTO vacas (ide,anio_nacimiento,origen,clase,estado,ide_madre,observaciones)
                      VALUES (?,?,?,?,?,?,?)''',
                   (ide, data.get('anio_nacimiento') or None, data.get('origen') or None,
                    data.get('clase') or None, 'Activa',
                    data.get('ide_madre') or None, data.get('observaciones') or None))
        db.commit()
        db.close()
        return jsonify({'ok': True, 'msg': f'✓ Vaca {ide} registrada.', 'ide': ide})
    db.close()
    return render_template('nueva_vaca.html')

# ─── DASHBOARD ───────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    db = get_db()
    temporada = int(request.args.get('temporada', 2024))

    # % preñez por toro (IATF)
    toros_iatf = db.execute('''
        SELECT toro_iatf as toro,
               COUNT(*) as total,
               SUM(CASE WHEN diagnostico_iatf IN ('PRENA','Preñada','PREÑADA','SUPERFICIAL','PROFUNDO') THEN 1 ELSE 0 END) as prenadas
        FROM eventos WHERE temporada=? AND toro_iatf IS NOT NULL AND toro_iatf NOT IN ('ENTORE','')
        GROUP BY toro_iatf ORDER BY prenadas DESC
    ''', (temporada,)).fetchall()

    # % preñez por toro (entore)
    toros_entore = db.execute('''
        SELECT toro_entore as toro,
               COUNT(*) as total,
               SUM(CASE WHEN eco_entore IN ('GRANDE','CHICA','PREÑADA','Preñada') THEN 1 ELSE 0 END) as prenadas
        FROM eventos WHERE temporada=? AND toro_entore IS NOT NULL AND toro_entore NOT IN ('ENTORE','-','')
        GROUP BY toro_entore ORDER BY prenadas DESC
    ''', (temporada,)).fetchall()

    # GMD promedio por temporada
    gmd_data = db.execute('''
        SELECT temporada, ROUND(AVG(gmd),3) as gmd_prom, COUNT(*) as n
        FROM terneros WHERE gmd IS NOT NULL AND gmd > 0
        GROUP BY temporada ORDER BY temporada
    ''').fetchall()

    # Vacas candidatas a baja (vacías 2 temporadas seguidas)
    candidatas = db.execute('''
        SELECT v.ide, v.anio_nacimiento, v.origen,
               GROUP_CONCAT(e.temporada || ':' || COALESCE(e.eco_entore, e.diagnostico_iatf,'?'), ' | ') as resumen
        FROM vacas v
        JOIN eventos e ON v.ide = e.ide_vaca
        WHERE v.estado = 'Activa'
        GROUP BY v.ide
        HAVING SUM(CASE WHEN e.eco_entore IN ('VACIA','Vacía') OR e.diagnostico_iatf='CICLA' THEN 1 ELSE 0 END) >= 2
        ORDER BY v.ide LIMIT 30
    ''').fetchall()

    temporadas = [r['temporada'] for r in db.execute(
        "SELECT DISTINCT temporada FROM eventos ORDER BY temporada DESC").fetchall()]

    db.close()
    return render_template('dashboard.html',
                           toros_iatf=toros_iatf, toros_entore=toros_entore,
                           gmd_data=gmd_data, candidatas=candidatas,
                           temporada=temporada, temporadas=temporadas)

# ─── API: verificar IDE ───────────────────────────────────
@app.route('/api/vaca/<ide>')
def api_vaca(ide):
    db = get_db()
    ide_clean = ide.strip().replace(' ','')
    vaca = db.execute("SELECT ide, anio_nacimiento, clase, estado FROM vacas WHERE ide=?",
                      (ide_clean,)).fetchone()
    db.close()
    if vaca:
        return jsonify({'encontrada': True, 'ide': vaca['ide'],
                        'anio': vaca['anio_nacimiento'], 'clase': vaca['clase'],
                        'estado': vaca['estado']})
    return jsonify({'encontrada': False})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
