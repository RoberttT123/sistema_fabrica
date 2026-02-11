from modules.database import ejecutar_consulta

def crear_tabla_produccion_crudo():
    print("🏗️  Preparando la creación de la tabla 'produccion_crudo'...")
    
    # Definición de la tabla basada en tu formato de "Planchado en Crudo"
    # fecha: Día del proceso
    # n_maquina: Corresponde a #MAQ
    # item: El tipo de media (Soporte Lycra, etc.)
    # n_partidas: Cantidad de bolsas (#PARTIDAS)
    # docenas: Cantidad planchada (DOCENAS)
    query = """
    CREATE TABLE IF NOT EXISTS produccion_crudo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATE DEFAULT CURRENT_DATE,
        n_maquina INTEGER NOT NULL,
        item TEXT NOT NULL,
        n_partidas INTEGER NOT NULL,
        docenas REAL NOT NULL
    )
    """
    
    try:
        ejecutar_consulta(query)
        print("✅ Tabla 'produccion_crudo' creada exitosamente.")
        print("📋 Campos: id, fecha, n_maquina, item, n_partidas, docenas.")
        
    except Exception as e:
        print(f"❌ Error al crear la tabla: {e}")

if __name__ == "__main__":
    crear_tabla_produccion_crudo()