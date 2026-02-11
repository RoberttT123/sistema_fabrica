from modules.database import ejecutar_consulta

def eliminar_tabla_antigua():
    print("🗑️  Preparando la eliminación de la tabla 'productos'...")
    
    try:
        # 1. Eliminar la tabla completa
        ejecutar_consulta("DROP TABLE IF EXISTS productos")
        
        # 2. Limpiar el registro de secuencias (opcional, para orden)
        ejecutar_consulta("DELETE FROM sqlite_sequence WHERE name='productos'")
        
        print("✅ Tabla 'productos' eliminada exitosamente.")
        print("📂 Ahora tu base de datos solo usará la tabla 'inventario'.")
        
    except Exception as e:
        print(f"❌ Error al intentar eliminar la tabla: {e}")

if __name__ == "__main__":
    eliminar_tabla_antigua()