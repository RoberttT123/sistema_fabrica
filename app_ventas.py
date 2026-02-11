import streamlit as st
import os
import time
from modules.auth import login, logout
from modules.clientes import render_clientes
from modules.trabajadores import render_trabajadores
from modules.inventario import render_inventario
from modules.medias_crudo import render_medias_crudo # Importación del nuevo módulo
from modules.pedidos import realizar_pedido
from modules.reportes import render_reportes
from modules.catalogo import render_catalogo 

# 1. Configuración de la página
st.set_page_config(
    page_title="Fábrica de Medias - Sistema de Producción", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 2. CSS para ocultar Deploy y Menú de 3 puntos (Lado derecho)
st.markdown("""
    <style>
        /* Oculta el contenedor de la derecha (Deploy y puntos) */
        .stAppDeployButton, 
        #MainMenu, 
        header [data-testid="stHeaderActionElements"] {
            display: none !important;
        }
        /* Asegura que el header sea transparente para no estorbar */
        header {
            background-color: rgba(0,0,0,0);
        }
    </style>
""", unsafe_allow_html=True)

def main():
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
    
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    if not st.session_state.autenticado:
        st.sidebar.title("Navegación")
        opcion_publica = st.sidebar.radio("Ir a:", ["🛍️ Ver Catálogo", "🔐 Acceso Personal"])
        
        if opcion_publica == "🛍️ Ver Catálogo":
            render_catalogo()
        else:
            login()
            
    else:
        # --- BARRA LATERAL PARA USUARIOS AUTENTICADOS ---
        st.sidebar.title(f"👋 Hola, {st.session_state.usuario}")
        st.sidebar.info(f"Rol actual: **{st.session_state.rol}**")
        st.sidebar.markdown("---")
        
        # Inicializar la elección por defecto si no existe
        if 'menu_choice' not in st.session_state:
            st.session_state.menu_choice = "Dashboard"

        # --- BOTONES PARA EL ROL JEFE ---
        if st.session_state.rol == "Jefe":
            if st.sidebar.button("📊 Dashboard / Reportes", use_container_width=True):
                st.session_state.menu_choice = "Dashboard"

            # NUEVO BOTÓN: Medias Crudo
            if st.sidebar.button("🧶 Producción Crudo", use_container_width=True):
                st.session_state.menu_choice = "MediasCrudo"
            
            if st.sidebar.button("👥 Clientes", use_container_width=True):
                st.session_state.menu_choice = "Clientes"
                
            if st.sidebar.button("👷 Trabajadores", use_container_width=True):
                st.session_state.menu_choice = "Trabajadores"
            
            if st.sidebar.button("📦 Inventario de Medias", use_container_width=True):
                st.session_state.menu_choice = "Inventario"
            
            if st.sidebar.button("🛒 Realizar Pedido", use_container_width=True):
                st.session_state.menu_choice = "Pedido"
                
            if st.sidebar.button("🛍️ Ver Catálogo Público", use_container_width=True):
                st.session_state.menu_choice = "Catalogo"
        
        else:
            # Menú simplificado para empleados
            menu_emp = ["🧶 Producción Crudo", "📦 Inventario de Medias", "🛒 Realizar Pedido"]
            choice_emp = st.sidebar.radio("Menú Principal", menu_emp)
            
            # Mapeo de elección de radio a menu_choice
            if choice_emp == "🧶 Producción Crudo": st.session_state.menu_choice = "MediasCrudo"
            elif choice_emp == "📦 Inventario de Medias": st.session_state.menu_choice = "Inventario"
            elif choice_emp == "🛒 Realizar Pedido": st.session_state.menu_choice = "Pedido"

        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()

        # --- LÓGICA DE NAVEGACIÓN (RENDERIZADO) ---
        choice = st.session_state.menu_choice

        if choice == "Dashboard":
            render_reportes()
            
        elif choice == "MediasCrudo":
            render_medias_crudo()
            
        elif choice == "Clientes":
            render_clientes()
            
        elif choice == "Trabajadores":
            render_trabajadores()
            
        elif choice == "Inventario":
            render_inventario()
            
        elif choice == "Pedido":
            realizar_pedido()
            
        elif choice == "Catalogo":
            render_catalogo()

if __name__ == "__main__":
    main()