import streamlit as st
import os
import time
from modules.auth import login, logout
from modules.usuarios_logic import gestionar_usuarios
from modules.inventario import render_inventario
from modules.pedidos import realizar_pedido
from modules.reportes import render_reportes
from modules.catalogo import render_catalogo  # Asegúrate de crear este archivo

# 1. Configuración de la página (Debe ser la primera instrucción de Streamlit)
st.set_page_config(
    page_title="Fábrica de Medias - Catálogo y Sistema", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

def main():
    # --- LOGO EN LA BARRA LATERAL ---
    if os.path.exists("logo.png"):
        st.sidebar.image("logo.png", use_container_width=True)
    
    # 2. Inicialización de variables de sesión
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False

    # --- 3. LÓGICA DE NAVEGACIÓN PÚBLICA (CLIENTES) vs PRIVADA (PERSONAL) ---
    
    if not st.session_state.autenticado:
        # Menú para personas que NO han iniciado sesión
        st.sidebar.title("Navegación")
        opcion_publica = st.sidebar.radio("Ir a:", ["🛍️ Ver Catálogo", "🔐 Acceso Personal"])
        
        if opcion_publica == "🛍️ Ver Catálogo":
            render_catalogo()  # Los clientes ven los productos aquí
        else:
            login()  # Aquí se muestra el formulario de login
            
    else:
        # --- 4. BARRA LATERAL PARA USUARIOS AUTENTICADOS ---
        st.sidebar.title(f"👋 Hola, {st.session_state.usuario}")
        st.sidebar.info(f"Rol actual: **{st.session_state.rol}**")
        st.sidebar.markdown("---")
        
        # Definición de Menú según Rol
        if st.session_state.rol == "Jefe":
            menu = [
                "📊 Dashboard / Reportes", 
                "👥 Usuarios y Clientes", 
                "📦 Inventario de Medias", 
                "🛒 Realizar Pedido", 
                "🛍️ Ver Catálogo Público"
            ]
        else:
            # El empleado solo ve lo necesario para registrar asistencia e inventario
            # El "Registro de Asistencia" suele estar dentro de gestionar_usuarios
            menu = ["👥 Asistencia", "📦 Inventario de Medias", "🛒 Realizar Pedido"]

        choice = st.sidebar.radio("Menú Principal", menu)
        
        st.sidebar.markdown("---")
        if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
            logout()

        # --- 5. RENDERIZADO DE MÓDULOS SEGÚN SELECCIÓN ---
        
        if choice == "📊 Dashboard / Reportes":
            render_reportes()
            
        elif choice == "👥 Usuarios y Clientes" or choice == "👥 Asistencia":
            # Nota: Si el rol es empleado, gestionar_usuarios() mostrará solo la pestaña de asistencia
            gestionar_usuarios()
            
        elif choice == "📦 Inventario de Medias":
            render_inventario()
            
        elif choice == "🛒 Realizar Pedido":
            realizar_pedido()
            
        elif choice == "🛍️ Ver Catálogo Público":
            render_catalogo()

# 6. Verificación de archivo de base de datos (Útil para depuración en la nube)
def check_database():
    if not os.path.exists('sistema_ventas.db'):
        st.error("⚠️ No se encontró el archivo 'sistema_ventas.db'. Por favor, asegúrate de subirlo a GitHub.")

if __name__ == "__main__":
    # check_database() # Descomenta esta línea si quieres verificar la DB al iniciar
    main()