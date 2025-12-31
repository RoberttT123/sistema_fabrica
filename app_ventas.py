import streamlit as st
import os
from modules.auth import login, logout
from modules.usuarios_logic import gestionar_usuarios
from modules.inventario import render_inventario
from modules.pedidos import realizar_pedido

from modules.reportes import render_reportes

# Configuración de la página
st.set_page_config(page_title="Sistema de Ventas - Fábrica de Medias", layout="wide")

def main():
    # --- LOGO EN LA BARRA LATERAL ---
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
    
    # Verificación de Sesión
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        login()
    else:
        # --- BARRA LATERAL DE NAVEGACIÓN ---
        st.sidebar.title(f"Bienvenido, {st.session_state.usuario}")
        st.sidebar.write(f"Rol: **{st.session_state.rol}**")
        st.sidebar.markdown("---")
        
        # Opciones de Menú según Rol
        menu = []
        if st.session_state.rol == "Jefe":
            menu = ["📊 Dashboard / Reportes", "👥 Usuarios y Clientes", "📦 Inventario de Medias", "🛒 Realizar Pedido", "📋 Historial de Ventas"]
        else:
            # El empleado solo ve lo necesario para trabajar
            menu = ["📦 Inventario de Medias", "🛒 Realizar Pedido"]

        choice = st.sidebar.radio("Seleccione una opción", menu)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión"):
            logout()

        # --- LÓGICA DE RENDERIZADO DE MÓDULOS ---
        if choice == "📊 Dashboard / Reportes":
            render_reportes()
            
        elif choice == "👥 Usuarios y Clientes":
            gestionar_usuarios()
            
        elif choice == "📦 Inventario de Medias":
            render_inventario()
            
        elif choice == "🛒 Realizar Pedido":
            realizar_pedido()
            


if __name__ == "__main__":
    main()