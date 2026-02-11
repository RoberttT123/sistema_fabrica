import streamlit as st
import requests
import urllib.parse
import os

# --- CONFIGURACIÓN ---
NUMERO_WHATSAPP = "59178790265" 

# 1. ACTUALIZACIÓN DE COLORES: Añadimos los nuevos tonos de Stretch y Panty
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

def obtener_productos_api(linea, tamano, color):
    # Asegúrate de usar el puerto correcto (8000 u 8001 según tu API activa)
    url = "http://localhost:8001/productos"
    params = {
        "linea": linea if linea != "Todos" else None,
        "tamano": tamano if tamano != "Todos" else None,
        "color": color if color != "Todos" else None
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        return []
    return []

def render_catalogo():
    st.markdown("<h1 style='text-align: center; color: #D44270;'>🧦 Catálogo de Fábrica</h1>", unsafe_allow_html=True)
    st.divider()

    # --- 2. ACTUALIZACIÓN DE FILTROS ---
    st.sidebar.header("🔍 Filtros de Búsqueda")
    
    f_linea = st.sidebar.selectbox("Línea", ["Todos", "Lycra", "Panty", "Stretch"])
    
    # Filtro de tipo dinámico según la línea
    opciones_tipo = ["Todos"]
    if f_linea == "Lycra":
        opciones_tipo += ["Soporte Lycra", "Pantalon Lycra"]
    elif f_linea == "Panty":
        opciones_tipo += ["Panty Grande", "Panty Mediano"]
    elif f_linea == "Stretch":
        opciones_tipo += ["Soporte Stretch", "Pantalon Stretch"]
    
    f_tamano = st.sidebar.selectbox("Tipo de Media", opciones_tipo)
    
    # Filtro de color con la nueva lista extendida
    f_color = st.sidebar.selectbox("Color", ["Todos"] + sorted(list(COLORES_HEX.keys())))

    # --- OBTENCIÓN Y RENDER ---
    productos = obtener_productos_api(f_linea, f_tamano, f_color)

    if not productos:
        st.info("💡 No hay stock con esos filtros.")
        return

    cols = st.columns(3)
    for i, prod in enumerate(productos):
        # Datos seguros
        val_nombre = prod.get('nombre', 'Sin nombre')
        val_linea = prod.get('linea', 'General')
        val_color = prod.get('color', 'Piel')
        val_stock = prod.get('stock', 0)
        val_precio = prod.get('precio_venta', 0.0)

        with cols[i % 3]:
            with st.container(border=True):
                # Imagen dinámica (formato: lycra_soporte_lycra_piel.jpg)
                # O simplemente por línea y color si prefieres
                nombre_img = f"{val_linea.lower()}_{val_color.lower().replace(' ', '_')}.jpg"
                path_img = f"assets/{nombre_img}"

                if os.path.exists(path_img):
                    st.image(path_img, use_container_width=True)
                else:
                    mostrar_color_alternativo(val_color)

                st.subheader(val_nombre)
                st.write(f"**🎨 Color:** {val_color}")
                st.write(f"**📦 Stock:** {int(val_stock)} Docenas")
                st.write(f"**💰 Precio:** :green[{val_precio:.2f} Bs]")
                
                link_wa = generar_link_whatsapp(val_nombre, val_precio, val_color, val_linea)
                st.link_button("💬 Consultar", link_wa, use_container_width=True, type="primary")

    st.markdown("---")
    st.caption(f"Sincronizado con Inventario Real")