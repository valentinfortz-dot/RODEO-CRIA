import json, os, sqlite3

DB_PATH = os.environ.get('DB_PATH', 'rodeo.db')
SEED_PATH = os.path.join(os.path.dirname(__file__), 'seed_data.json')

def seed_if_empty():
    if not os.path.exists(SEED_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM vacas").fetchone()[0]
    if count > 0:
        conn.close()
        return
    print("Cargando datos históricos...")
    with open(SEED_PATH) as f:
        data = json.load(f)
    c = conn.cursor()
    for r in data['toros']:
        c.execute('INSERT OR IGNORE INTO toros (ide,idv,nombre,ce,aptitud,edad,origen,padre,notas) VALUES (?,?,?,?,?,?,?,?,?)',
                  (r['ide'],r['idv'],r['nombre'],r['ce'],r['aptitud'],r['edad'],r['origen'],r['padre'],r['notas']))
    for r in data['vacas']:
        c.execute('INSERT OR IGNORE INTO vacas (ide,anio_nacimiento,origen,clase,estado,motivo_baja,ide_madre,observaciones) VALUES (?,?,?,?,?,?,?,?)',
                  (r['ide'],r['anio_nacimiento'],r['origen'],r['clase'],r['estado'],r['motivo_baja'],r['ide_madre'],r['observaciones']))
    for r in data['eventos']:
        c.execute('INSERT INTO eventos (ide_vaca,temporada,dao_sincro,toro_iatf,diagnostico_iatf,ecografia_final,toro_entore,eco_entore,caravana_ternero,observaciones) VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (r['ide_vaca'],r['temporada'],r['dao_sincro'],r['toro_iatf'],r['diagnostico_iatf'],r['ecografia_final'],r['toro_entore'],r['eco_entore'],r['caravana_ternero'],r['observaciones']))
    for r in data['terneros']:
        c.execute('INSERT INTO terneros (caravana,ide_madre,temporada,sexo,raza,semana_nacimiento,potrero,peso_destete,fecha_destete,dias_destete,gmd) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                  (r['caravana'],r['ide_madre'],r['temporada'],r['sexo'],r['raza'],r['semana_nacimiento'],r['potrero'],r['peso_destete'],r['fecha_destete'],r['dias_destete'],r['gmd']))
    conn.commit()
    conn.close()
    print(f"Datos cargados: {len(data['vacas'])} vacas, {len(data['eventos'])} eventos")
