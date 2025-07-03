import sqlite3
from datetime import datetime

# Conectar a la base de datos original
orig_conn = sqlite3.connect('instance/riego_backup.db')
orig_cursor = orig_conn.cursor()

# Crear nueva base de datos
new_conn = sqlite3.connect('instance/riego.db')
new_cursor = new_conn.cursor()

# Crear nuevas tablas
new_cursor.execute('''
    CREATE TABLE IF NOT EXISTS riego_config (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auto BOOLEAN NOT NULL,
        fecha DATETIME
    )
''')

# Copiar datos existentes
for table in ['sensor_data', 'riego_estado', 'sistema_estado', 'riego_manual']:
    new_cursor.execute(f"DROP TABLE IF EXISTS {table}")
    orig_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}'")
    create_sql = orig_cursor.fetchone()[0]
    new_cursor.execute(create_sql)
    
    orig_cursor.execute(f"SELECT * FROM {table}")
    rows = orig_cursor.fetchall()
    
    if rows:
        cols = len(rows[0])
        placeholders = ','.join(['?'] * cols)
        new_cursor.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)

# Agregar configuración inicial para riego automático
new_cursor.execute("INSERT INTO riego_config (auto, fecha) VALUES (?, ?)", 
                  (False, datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')))

# Guardar cambios
new_conn.commit()
orig_conn.close()
new_conn.close()

print("Migración completada exitosamente!")
