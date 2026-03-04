import streamlit as st
import time
import os
import pandas as pd
from modules.database import ejecutar_consulta, obtener_datos, registrar_log
from datetime import datetime
from fpdf import FPDF

def render_trabajadores():
    """
    Gestión de personal, salarios y control de asistencia con PostgreSQL.
    """
    st.header("👷 Panel de Personal y Asistencia")
    
    tab_gestion, tab_asistencia = st.tabs([
        "⚙️ Gestión de Personal", 
        "🕒 Control de Asistencia"
    ])

    # --- 1. PESTAÑA: GESTIÓN DE PERSONAL ---
    with tab_gestion:
        st.subheader("Registrar Nuevo Empleado")
        with st.form("form_registro_trabajador", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre = st.text_input("Nombre Completo")
                usuario = st.text_input("Usuario (Login)")
                clave = st.text_input("Contraseña", type="password")
            with col_b:
                salario = st.number_input("Salario Mensual (Bs)", min_value=0.0, step=10.0)
                telefono = st.text_input("Teléfono de Contacto")
            
            if st.form_submit_button("✅ Guardar Empleado", use_container_width=True):
                if nombre and usuario and clave:
                    # Verificar si el usuario ya existe en Supabase
                    check = obtener_datos("SELECT id_usuario FROM usuarios WHERE usuario = %s", (usuario,))
                    if not check.empty:
                        st.error("❌ El nombre de usuario ya está en uso.")
                    else:
                        query = """
                            INSERT INTO usuarios (nombre, rol, usuario, contrasena, salario, telefono) 
                            VALUES (%s, 'Empleado', %s, %s, %s, %s)
                        """
                        ejecutar_consulta(query, (nombre, usuario, clave, salario, telefono))
                        
                        # --- LOG DE AUDITORÍA ---
                        registrar_log("INSERT", "usuarios", f"Registró al empleado: {nombre} (User: {usuario})")
                        
                        st.success(f"¡Empleado {nombre} registrado correctamente!")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Por favor, complete los campos obligatorios: Nombre, Usuario y Clave.")

        st.divider()

        # Edición y Baja
        with st.expander("🛠️ Administrar Personal Existente"):
            id_edit = st.number_input("Ingrese ID del Trabajador para editar:", min_value=1, step=1)
            emp_data = obtener_datos("SELECT * FROM usuarios WHERE id_usuario = %s AND rol = 'Empleado'", (id_edit,))
            
            if not emp_data.empty:
                with st.form("edit_worker_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1: n_nom = st.text_input("Nombre", value=emp_data.iloc[0]['nombre'])
                    with c2: n_sal = st.number_input("Salario (Bs)", value=float(emp_data.iloc[0]['salario'] or 0))
                    with c3: n_tel = st.text_input("Teléfono", value=emp_data.iloc[0]['telefono'] or "")
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        ejecutar_consulta(
                            "UPDATE usuarios SET nombre=%s, salario=%s, telefono=%s WHERE id_usuario=%s", 
                            (n_nom, n_sal, n_tel, id_edit)
                        )
                        # --- LOG DE AUDITORÍA ---
                        registrar_log("UPDATE", "usuarios", f"Actualizó datos/salario del trabajador ID {id_edit}: {n_nom}")
                        
                        st.success("Información actualizada."); time.sleep(1); st.rerun()
                    
                    if b2.form_submit_button("🗑️ Dar de Baja", type="primary", use_container_width=True):
                        ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=%s", (id_edit,))
                        
                        # --- LOG DE AUDITORÍA ---
                        registrar_log("DELETE", "usuarios", f"ELIMINÓ al trabajador ID {id_edit} de la nómina")
                        
                        st.warning("Trabajador eliminado de la base de datos."); time.sleep(1); st.rerun()
            else:
                st.caption("Escriba el ID de un trabajador para habilitar la edición.")

        st.write("### 📋 Nómina Actual")
        df_users = obtener_datos("""
            SELECT id_usuario as "ID", nombre as "Nombre", usuario as "Usuario", 
                   salario as "Salario (Bs)", telefono as "Teléfono" 
            FROM usuarios 
            WHERE rol = 'Empleado' 
            ORDER BY id_usuario ASC
        """)
        st.dataframe(df_users, use_container_width=True, hide_index=True)

    # --- 2. PESTAÑA: CONTROL DE ASISTENCIA ---
    with tab_asistencia:
        render_asistencia_logic()

def render_asistencia_logic():
    st.subheader("🕒 Reporte de Asistencia Semanal")
    
    turno_ver = st.radio("Turno a consultar:", ["Mañana (Entrada 08:30)", "Tarde (Entrada 14:00)"], horizontal=True)
    
    # Parámetros de turno para PostgreSQL
    if "Mañana" in turno_ver:
        r_ini, r_fin, h_limite = "06:00:00", "13:00:00", "08:31"
    else:
        r_ini, r_fin, h_limite = "13:01:00", "20:00:00", "14:01"

    # CONSULTA SQL AVANZADA PARA POSTGRESQL
    query_turnos = f"""
        SELECT 
            nombre_usuario as "Empleado",
            MIN(CASE WHEN EXTRACT(DOW FROM fecha_hora) = 1 THEN TO_CHAR(fecha_hora, 'HH24:MI') END) as "Lun",
            MIN(CASE WHEN EXTRACT(DOW FROM fecha_hora) = 2 THEN TO_CHAR(fecha_hora, 'HH24:MI') END) as "Mar",
            MIN(CASE WHEN EXTRACT(DOW FROM fecha_hora) = 3 THEN TO_CHAR(fecha_hora, 'HH24:MI') END) as "Mie",
            MIN(CASE WHEN EXTRACT(DOW FROM fecha_hora) = 4 THEN TO_CHAR(fecha_hora, 'HH24:MI') END) as "Jue",
            MIN(CASE WHEN EXTRACT(DOW FROM fecha_hora) = 5 THEN TO_CHAR(fecha_hora, 'HH24:MI') END) as "Vie",
            MIN(CASE WHEN EXTRACT(DOW FROM fecha_hora) = 6 THEN TO_CHAR(fecha_hora, 'HH24:MI') END) as "Sab"
        FROM registro_accesos
        WHERE fecha_hora::time BETWEEN '{r_ini}' AND '{r_fin}'
        GROUP BY nombre_usuario, EXTRACT(WEEK FROM fecha_hora), EXTRACT(YEAR FROM fecha_hora)
        ORDER BY "Empleado" ASC
    """
    
    df_turno = obtener_datos(query_turnos).fillna("-")

    if not df_turno.empty:
        # Estilo visual para atrasos en la tabla
        def color_atraso(val):
            if val != "-" and val > h_limite:
                return 'color: #ff4b4b; font-weight: bold;'
            return ''

        st.write(f"**Registros encontrados ({turno_ver}):**")
        st.dataframe(
            df_turno.style.applymap(color_atraso, subset=['Lun','Mar','Mie','Jue','Vie','Sab']), 
            use_container_width=True
        )
        
        # --- GENERACIÓN DE PDF ---
        if st.button(f"📥 Exportar Reporte {turno_ver} a PDF", use_container_width=True):
            pdf = FPDF(orientation='L')
            pdf.add_page()
            if os.path.exists("logo.png"):
                pdf.image("logo.png", x=10, y=8, w=20)
            
            pdf.set_font("Helvetica", 'B', 16)
            pdf.cell(0, 10, txt=f"REPORTE DE ASISTENCIA - {turno_ver.upper()}", ln=True, align='C')
            pdf.ln(10)
            
            pdf.set_font("Helvetica", 'B', 10)
            pdf.set_fill_color(220, 220, 220)
            titulos = ["Empleado", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab"]
            anchos = [70, 32, 32, 32, 32, 32, 32]
            for i in range(len(titulos)):
                pdf.cell(anchos[i], 10, titulos[i], 1, 0, 'C', True)
            pdf.ln()

            pdf.set_font("Helvetica", size=10)
            for _, row in df_turno.iterrows():
                pdf.set_text_color(0, 0, 0)
                pdf.cell(70, 10, str(row['Empleado']), 1)
                for dia in ['Lun','Mar','Mie','Jue','Vie','Sab']:
                    h = str(row[dia])
                    if h != "-" and h > h_limite:
                        pdf.set_text_color(200, 0, 0)
                    else:
                        pdf.set_text_color(0, 0, 0)
                    pdf.cell(32, 10, h, 1, 0, 'C')
                pdf.ln()
            
            res = pdf.output(dest='S')
            final_pdf = res.encode('latin-1', errors='replace') if isinstance(res, str) else res
            st.download_button(
                label="Click para descargar archivo", 
                data=final_pdf, 
                file_name=f"Asistencia_{turno_ver.split(' ')[0]}.pdf", 
                mime="application/pdf"
            )
    else:
        st.info(f"No se registran marcas de entrada para el turno {turno_ver} en la base de datos.")