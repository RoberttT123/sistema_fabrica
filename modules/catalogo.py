import streamlit as st
import urllib.parse
import os
# Importamos obtener_datos para leer directamente la DB sin depender de la API local
from modules.database import obtener_datos 

# --- CONFIGURACIÓN ---
NUMERO_WHATSAPP = "59178790265" 

COLORES_HEX = {
    "Piel": "#F5D0B9", "Coñac": "#9E5B3A", "Negro": "#1A1A1A",
    "Azul": "#002366", "Humo": "#737373", "Marrón": "#4B2E2A",
    "Romance": "#FFD1DC", "Tabaco": "#6B4226", "Acacia": "#EEDC82",
    "Carbón": "#36454F", "Blanco": "#FFFFFF", "Hueso blanco": "#F9F6EE",
    "Hueso rosado": "#F3E5E4", "Beige": "#F5F5DC", "Dumbo": "#8B8680",
    "Cartón": "#C2B280", "Calipso": "#00CCFF", "Chocolate": "#7B3F00",
    "Almendra": "#EED9C4", "Humo plata": "#BCC6CC", "Humo oscuro": "#54626F",
    "Uva": "#6A0DAD", "Api": "#722F37"
}

def mostrar_color_alternativo(color_nombre):
    color_hex = COLORES_HEX.get(color_nombre, "#CCCCCC")
    st.markdown(f"""
        <div style="display: flex; flex-direction: column; justify-content: center; align-items: center; 
                    height: 180px; background-color: #F8F9FA; border-radius: 15px; margin-bottom: 10px; border: 1px solid #EEEEEE;">
            <div style="width: 70px; height: 70px; background-color: {color_hex}; border-radius: 50%; 
                        border: 3px solid white; box-shadow: 0px 4px 12px rgba(0,0,0,0.15);"></div>
            <p style="margin-top: 15px; color: #666666; font-size: 14px; font-weight: 500;">Tono: {color_nombre}</p>
        </div>
    """, unsafe_allow_html=True)

def generar_link_whatsapp(producto, precio, color, linea):
    mensaje = (
        f"¡Hola! 👋 Me interesa este modelo de su catálogo:\n\n"
        f"✨ *Línea:* {linea}\n"
        f"📏 *Tipo:* {producto}\n"
        f"🎨 *Color:* {color}\n"
        f"💰 *Precio:* {precio:.2f} Bs\n\n"
        f"¿Tienen disponibilidad?"
    )
    return f"https://wa.me/{NUMERO_WHATSAPP}?text={urllib.parse.quote(mensaje)}"

# --- CORRECCIÓN CLAVE: LEER DIRECTO DE LA BASE DE DATOS ---
def obtener_productos_db(linea, tamano, color):
    query = "SELECT nombre, linea, tamano, color, cantidad as stock, precio_venta FROM inventario WHERE cantidad > 0"
    params = []

    if linea != "Todos":
        query += " AND linea = ?"
        params.append(linea)
    
    if tamano != "Todos":
        query += " AND tamano = ?"
        params.append(tamano)

    if color != "Todos":
        query += " AND color = ?"
        params.append(color)

    try:
        return obtener_datos(query, tuple(params))
    except Exception:
        return None

def render_catalogo():
    st.markdown("<h1 style='text-align: center; color: #D44270;'>🧦 Catálogo de Fábrica</h1>", unsafe_allow_html=True)
    st.divider()

    # --- FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    f_linea = st.sidebar.selectbox("Línea", ["Todos", "Lycra", "Panty", "Stretch"])
    
    opciones_tipo = ["Todos"]
    if f_linea == "Lycra": opciones_tipo += ["Soporte Lycra", "Pantalon Lycra"]
    elif f_linea == "Panty": opciones_tipo += ["Panty Grande", "Panty Mediano"]
    elif f_linea == "Stretch": opciones_tipo += ["Soporte Stretch", "Pantalon Stretch"]
    
    f_tamano = st.sidebar.selectbox("Tipo de Media", opciones_tipo)
    f_color = st.sidebar.selectbox("Color", ["Todos"] + sorted(list(COLORES_HEX.keys())))

    # Obtención de datos directa
    df_productos = obtener_productos_db(f_linea, f_tamano, f_color)

    if df_productos is None or df_productos.empty:
        st.info("💡 No hay stock con esos filtros en la base de datos.")
        return

    # Renderizado en columnas
    cols = st.columns(3)
    for i, (_, prod) in enumerate(df_productos.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                v_nombre = prod['nombre']
                v_linea = prod['linea']
                v_color = prod['color']
                v_stock = prod['stock']
                v_precio = prod['precio_venta']

                # Lógica de imagen o color
                nombre_img = f"{v_linea.lower()}_{v_color.lower().replace(' ', '_')}.jpg"
                path_img = f"assets/{nombre_img}"

                if os.path.exists(path_img):
                    st.image(path_img, use_container_width=True)
                else:
                    mostrar_color_alternativo(v_color)

                st.subheader(v_nombre)
                st.write(f"**🎨 Color:** {v_color}")
                st.write(f"**📦 Stock:** {int(v_stock)} Docenas")
                st.write(f"**💰 Precio:** :green[{v_precio:.2f} Bs]")
                
                link_wa = generar_link_whatsapp(v_nombre, v_precio, v_color, v_linea)
                st.link_button("💬 Consultar", link_wa, use_container_width=True, type="primary")