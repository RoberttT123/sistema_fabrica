from modules.database import ejecutar_consulta
from datetime import datetime

# Estructura completa de tu fábrica
ESTRUCTURA = {
    "Lycra": {
        "Soporte Lycra": ["Romance", "Piel", "Coñac", "Tabaco", "Acacia", "Carbón", "Humo"],
        "Pantalon Lycra": ["Romance", "Piel", "Coñac", "Tabaco"]
    },
    "Panty": {
        "Panty Grande": ["Romance", "Piel", "Coñac", "Tabaco", "Negro", "Blanco"],
        "Panty Mediano": ["Romance", "Piel", "Coñac", "Tabaco", "Negro"]
    },
    "Stretch": {
        "Soporte Stretch": ["Hueso blanco", "Hueso rosado", "Beige", "Dumbo", "Romance", "Coñac", "Tabaco", "Cartón", "Acacia", "Calipso", "Chocolate", "Almendra", "Humo plata", "Humo oscuro", "Uva", "Api", "Carbón", "Negro"],
        "Pantalon Stretch": ["Hueso blanco", "Hueso rosado", "Beige", "Dumbo", "Romance", "Coñac", "Tabaco", "Cartón", "Acacia", "Calipso", "Chocolate", "Almendra", "Humo plata", "Humo oscuro", "Uva", "Api", "Carbón", "Negro"]
    }
}

def poblar_inventario():
    print("🚀 Iniciando carga masiva de inventario...")
    hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    stock_inicial = 50
    precio_base = 25.00 # Puedes cambiar este precio
    
    contador = 0
    
    for linea, tipos in ESTRUCTURA.items():
        for tipo, colores in tipos.items():
            for color in colores:
                query = """
                    INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                # nombre = tipo para mantener consistencia
                ejecutar_consulta(query, (tipo, linea, tipo, color, stock_inicial, precio_base, hora_actual))
                contador += 1
                print(f"✅ Añadido: {linea} - {tipo} ({color})")

    print(f"\n✨ ¡Carga completada! Se crearon {contador} productos con 50 unidades cada uno.")

if __name__ == "__main__":
    poblar_inventario()