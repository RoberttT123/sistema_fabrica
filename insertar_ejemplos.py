from modules.database import ejecutar_consulta

def cargar_productos_reales():
    # Líneas de productos
    lineas = ["Nylon Lujo", "Soporte Licra"]
    # Tamaños/Largos
    largos = ["Falda (Sobre la rodilla)", "Pantalón (Pantorrilla)", "Tobillera"]
    # Colores
    colores = ["Piel", "Coñac", "Negro", "Azul", "Humo", "Marrón"]

    for linea in lineas:
        for largo in largos:
            for color in colores:
                nombre = f"Media {linea} - {largo}"
                descripcion = f"Media para dama de alta calidad, acabado elegante en color {color}."
                precio = 15.00 if "Nylon" in linea else 22.00 # Ejemplo de precios diferentes
                
                query = """
                    INSERT INTO productos (nombre, descripcion, precio_venta, color, stock, categoria) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """
                # Insertamos cada combinación con un stock inicial de 50
                ejecutar_consulta(query, (nombre, descripcion, precio, color, 50, linea))

    print("✅ ¡Catálogo de fábrica actualizado con éxito!")

if __name__ == "__main__":
    cargar_productos_reales()