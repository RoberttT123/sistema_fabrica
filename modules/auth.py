import streamlit as st
from modules.database import ejecutar_consulta, validar_usuario, obtener_datos
from datetime import datetime
import time

def login():
    st.markdown("<h1 style='text-align: center;'>🔐 Acceso Fábrica</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        with st.container(border=True):
            usuario = st.text_input("👤 Usuario", key="login_user", placeholder="Ingresa tu usuario")
            clave = st.text_input("🔑 Contraseña", type="password", key="login_pass", placeholder="******")
            
            if st.button("🚀 Entrar al Sistema", use_container_width=True):
                if not usuario or not clave:
                    st.warning("⚠️ Por favor, completa todos los campos.")
                    return

                user_data = validar_usuario(usuario, clave)
                
                if user_data:
                    # 1. Configurar variables de sesión
                    st.session_state.autenticado = True
                    st.session_state.id_usuario = user_data['id_usuario']
                    st.session_state.usuario = user_data['nombre']
                    st.session_state.rol = user_data['rol']
                    
                    nombre_user = st.session_state.usuario
                    ahora = datetime.now()
                    fecha_hoy = ahora.strftime("%Y-%m-%d")
                    hora_actual = ahora.time()

                    # --- LÓGICA DE REGISTRO POR TURNOS ---
                    # Mañana: 06:00 a 13:00 | Tarde: 13:01 a 19:00
                    rango_ini, rango_fin = ("06:00:00", "13:00:00") if hora_actual <= datetime.strptime("13:00:00", "%H:%M:%S").time() else ("13:01:00", "19:00:00")

                    # Consultamos si YA EXISTE algun registro hoy en este rango para este usuario
                    # Usamos COUNT(*) para evitar errores de nombres de columnas inexistentes
                    check_query = """
                        SELECT COUNT(*) as total 
                        FROM registro_accesos 
                        WHERE nombre_usuario = ? 
                        AND DATE(fecha_hora) = ? 
                        AND TIME(fecha_hora) BETWEEN ? AND ?
                    """
                    resultado = obtener_datos(check_query, (nombre_user, fecha_hoy, rango_ini, rango_fin))
                    
                    # Verificamos el conteo de registros existentes
                    ya_registro = resultado.iloc[0]['total'] > 0 if not resultado.empty else False

                    if not ya_registro:
                        # Si es la primera vez en el turno, guardamos la entrada
                        ejecutar_consulta(
                            "INSERT INTO registro_accesos (nombre_usuario, fecha_hora) VALUES (?, ?)", 
                            (nombre_user, ahora.strftime("%Y-%m-%d %H:%M:%S"))
                        )
                        st.success(f"✅ Entrada registrada: {ahora.strftime('%H:%M:%S')}")
                        st.toast(f"Asistencia guardada: {nombre_user}", icon='⏰')
                    else:
                        # Si ya entró antes, solo le damos la bienvenida
                        st.info(f"👋 Hola {nombre_user}, tu entrada ya está registrada.")
                    
                    time.sleep(1.2)
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos.")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()