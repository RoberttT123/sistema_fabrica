import streamlit as st
import os
import time
from modules.auth import login, logout
from modules.clientes import render_clientes
from modules.trabajadores import render_trabajadores
from modules.inventario import render_inventario
from modules.medias_crudo import render_medias_crudo 
from modules.pedidos import realizar_pedido
from modules.reportes import render_reportes
from modules.catalogo import render_catalogo 
from modules.auditoria import render_auditoria
# 1. Configuración de la página - Debe ser la primera instrucción
st.set_page_config(
    page_title="Fábrica de Medias - Cloud System", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="🧦"
)

st.markdown("""
    <style>
        /* 1. Barra superior totalmente transparente */
        header[data-testid="stHeader"] {
            background-color: rgba(0, 0, 0, 0) !important;
            border-bottom: none !important;
        }

        /* 2. Ocultar TODO el grupo de botones de la derecha (GitHub, Fork, Star, Share) */
        [data-testid="stHeaderActionElements"] {
            display: none !important;
        }

        /* 3. Ocultar específicamente el botón de 'Deploy' y 'Fork' */
        .stAppDeployButton {
            display: none !important;
        }

        /* 4. Ocultar el menú de usuario (tu cuenta) y los 3 puntos de la derecha */
        #MainMenu, 
        [data-testid="stToolbar"], 
        [data-testid="stDecoration"] {
            display: none !important;
        }

        /* 5. MANTENER VISIBLE EL BOTÓN DE MENÚ (>>) */
        /* Localizamos el botón que NO está en el grupo de acción de la derecha */
        header[data-testid="stHeader"] button:not([aria-label="share"]):not([aria-label="favorite"]) {
            color: white !important;
            opacity: 1 !important;
        }

        /* 6. Eliminar cualquier borde o sombra que delate la barra */
        [data-testid="stHeader"]::before {
            background-image: none !important;
            display: none !important;
        }

        /* 7. Pegar el contenido al tope de la pantalla */
        .block-container {
            padding-top: 0rem !important;
        }
    </style>
""", unsafe_allow_html=True)

def main():
    # Logo responsivo
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
    
    # Inicialización del estado de autenticación
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    # --- FLUJO PÚBLICO (SIN LOGIN) ---
    if not st.session_state.autenticado:
        st.sidebar.title("🌐 Navegación")
        opcion_publica = st.sidebar.radio(
            "Ir a:", 
            ["🛍️ Ver Catálogo", "🔐 Acceso Personal"],
            help="El catálogo es público para preventa. El acceso personal requiere credenciales."
        )
        
        if opcion_publica == "🛍️ Ver Catálogo":
            render_catalogo()
        else:
            login()
            
    # --- FLUJO PRIVADO (USUARIOS AUTENTICADOS) ---
    else:
        st.sidebar.title(f"👋 Hola, {st.session_state.usuario}")
        st.sidebar.markdown(f"**Rol:** `{st.session_state.rol}`")
        st.sidebar.markdown("---")
        
        # Inicializar la elección de menú si no existe
        if 'menu_choice' not in st.session_state:
            st.session_state.menu_choice = "Dashboard"

        # --- NAVEGACIÓN POR ROL: JEFE ---
        if st.session_state.rol == "Jefe":
            st.sidebar.subheader("💎 Panel Administrativo")
            
            if st.sidebar.button("📊 Dashboard / Reportes", use_container_width=True):
                st.session_state.menu_choice = "Dashboard"

            if st.sidebar.button("🧶 Producción Crudo", use_container_width=True):
                st.session_state.menu_choice = "MediasCrudo"
            
            if st.sidebar.button("👥 Gestión de Clientes", use_container_width=True):
                st.session_state.menu_choice = "Clientes"
                
            if st.sidebar.button("👷 Personal y Asistencia", use_container_width=True):
                st.session_state.menu_choice = "Trabajadores"
            
            if st.sidebar.button("📦 Inventario de Medias", use_container_width=True):
                st.session_state.menu_choice = "Inventario"
            
            if st.sidebar.button("🛒 Registrar Pedido", use_container_width=True):
                st.session_state.menu_choice = "Pedido"
                
            if st.sidebar.button("🛍️ Ver Catálogo", use_container_width=True):
                st.session_state.menu_choice = "Catalogo"

            if st.sidebar.button("🕵️ Auditoría de Sistema", use_container_width=True):
                st.session_state.menu_choice = "Auditoria"
        
        # --- NAVEGACIÓN POR ROL: EMPLEADO ---
        else:
            st.sidebar.subheader("🛠️ Operaciones")
            menu_emp = ["🧶 Producción Crudo", "📦 Inventario de Medias", "🛒 Realizar Pedido"]
            choice_emp = st.sidebar.radio("Selecciona una tarea:", menu_emp)
            
            # Sincronizar elección del radio con el estado global
            mapping = {
                "🧶 Producción Crudo": "MediasCrudo",
                "📦 Inventario de Medias": "Inventario",
                "🛒 Realizar Pedido": "Pedido"
            }
            st.session_state.menu_choice = mapping[choice_emp]

        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
            logout()

        # --- LÓGICA DE RENDERIZADO DINÁMICO ---
        # Este bloque decide qué archivo .py mostrar basándose en la elección del menú
        choice = st.session_state.menu_choice

        try:
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
            elif choice == "Auditoria":
                render_auditoria()
        except Exception as e:
            st.error(f"⚠️ Error al cargar el módulo {choice}: {e}")
            st.info("Intenta recargar la página o contacta al administrador.")

if __name__ == "__main__":
    main()