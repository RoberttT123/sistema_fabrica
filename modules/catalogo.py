import streamlit as st
from modules.database import obtener_datos
import os
import urllib.parse

def generar_link_whatsapp(producto, precio, color):
    """Genera un link de WhatsApp con un mensaje predefinido."""
    # ⚠️ REEMPLAZA CON TU NÚMERO (Ejemplo para Bolivia: 59170000000)
    # Sin el signo +, solo números.
    telefono = "591XXXXXXXX" 
    
    mensaje = (
        f"¡Hola! 👋 Vi tu catálogo web y me interesa este producto:\n\n"
        f"🧦 *Producto:* {producto}\n"
        f"🎨 *Color:* {color}\n"
        f"💰 *Precio:* {precio} Bs\n\n"
        f"¿Tienen disponibilidad?"
    )
    
    # Codificar el mensaje para que sea válido en una URL
    mensaje_url = urllib.parse.quote(mensaje)
    return f"https://wa.me/{telefono}?text={mensaje_url}"

def render_catalogo():
    st.markdown("<h1 style='text-align: center;'>🛍️ Nuestro Catálogo de Medias</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Bienvenido a nuestra tienda virtual. Haz tu pedido directo por WhatsApp.</p>", unsafe_allow_html=True)
    st.divider()

    # Obtenemos los productos con stock disponible
    query = "SELECT nombre, descripcion, precio_venta, color, stock FROM productos WHERE stock > 0"
    df_productos = obtener_datos(query)

    if not df_productos.empty:
        # Creamos una cuadrícula de 3 columnas
        cols = st.columns(3)
        
        for index, row in df_productos.iterrows():
            with cols[index % 3]:
                # Tarjeta de producto con borde usando st.container
                with st.container(border=True):
                    st.markdown(f"### {row['nombre']}")
                    
                    # --- LÓGICA DE IMAGEN ---
                    # Buscamos la imagen en la carpeta 'assets' con el nombre del producto
                    # Ejemplo: "Media Escolar" -> "assets/media_escolar.jpg"
                    nombre_archivo = row['nombre'].lower().replace(' ', '_')
                    foto_path = f"assets/{nombre_archivo}.jpg"
                    
                    if os.path.exists(foto_path):
                        st.image(foto_path, use_container_width=True)
                    else:
                        # Si no hay foto, ponemos un cuadro gris con texto
                        st.image("https://via.placeholder.com/300x300.png?text=Sin+Foto", use_container_width=True)
                    
                    # --- DETALLES ---
                    st.write(f"**🎨 Color:** {row['color']}")
                    st.write(f"**💰 Precio:** {row['precio_venta']} Bs")
                    st.caption(f"📝 {row['descripcion']}")
                    
                    # --- BOTÓN DE WHATSAPP ---
                    link_wa = generar_link_whatsapp(row['nombre'], row['precio_venta'], row['color'])
                    
                    st.link_button(
                        label="💬 Pedir por WhatsApp",
                        url=link_wa,
                        use_container_width=True,
                        type="primary"
                    )
    else:
        st.info("📦 Por el momento no tenemos stock disponible. ¡Vuelve pronto!")