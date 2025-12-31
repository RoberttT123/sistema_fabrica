import streamlit as st
from modules.database import obtener_datos
import os

def render_catalogo():
    st.header("🛍️ Nuestro Catálogo de Medias")
    st.write("Bienvenido a nuestra tienda virtual. Selecciona tus productos y haz tu pedido.")

    # Obtenemos los productos del inventario
    # Filtramos solo lo necesario para el cliente
    query = "SELECT nombre, descripcion, precio_venta, color, stock FROM productos WHERE stock > 0"
    df_productos = obtener_datos(query)

    if not df_productos.empty:
        # Mostramos los productos en una cuadrícula (grid) de 3 columnas
        cols = st.columns(3)
        
        for index, row in df_productos.iterrows():
            with cols[index % 3]:
                st.subheader(row['nombre'])
                
                # Intentar mostrar una imagen si existe
                foto_path = f"assets/{row['nombre'].lower().replace(' ', '_')}.jpg"
                if os.path.exists(foto_path):
                    st.image(foto_path, use_container_width=True)
                else:
                    st.info("📷 Imagen en proceso")
                
                st.write(f"**Color:** {row['color']}")
                st.write(f"**Precio:** {row['precio_venta']} Bs")
                
                if st.button(f"Pedir {row['nombre']}", key=f"btn_{index}"):
                    st.success(f"¡Añadido! (Aquí podemos conectar un formulario de WhatsApp)")
    else:
        st.warning("Por el momento no tenemos stock disponible.")