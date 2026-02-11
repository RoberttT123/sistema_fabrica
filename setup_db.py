from modules.database import ejecutar_consulta

print("🧹 Iniciando limpieza profunda del inventario...")

try:
    # 1. Borra todos los registros de la tabla CORRECTA
    ejecutar_consulta("DELETE FROM inventario")

    # 2. Resetea los contadores de ID para que el próximo producto sea el ID 1
    ejecutar_consulta("DELETE FROM sqlite_sequence WHERE name='inventario'")

    print("✅ ¡Éxito! La tabla 'inventario' está vacía y los IDs reseteados.")
    print("🚀 Ahora puedes ejecutar tu script de 'Carga Masiva' para repoblar todo.")

except Exception as e:
    print(f"❌ Error al limpiar: {e}")