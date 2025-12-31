import sqlite3

def reparar_tabla_pedidos():
    conn = sqlite3.connect('sistema_ventas.db')
    cursor = conn.cursor()
    try:
        # Añadimos la columna que falta para conectar con el inventario de medias
        cursor.execute("ALTER TABLE pedidos ADD COLUMN id_inventario INTEGER")
        conn.commit()
        print("✅ Columna 'id_inventario' añadida exitosamente.")
    except sqlite3.OperationalError:
        print("ℹ️ La columna ya existe, no es necesario hacer cambios.")
    finally:
        conn.close()

if __name__ == "__main__":
    reparar_tabla_pedidos()