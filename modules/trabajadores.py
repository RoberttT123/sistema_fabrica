import streamlit as st
import time
import os
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime
from fpdf import FPDF

def render_trabajadores():
    """
    Módulo independiente para la gestión de trabajadores, salarios y control de asistencia.
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
                    # Verificar si el usuario ya existe
                    check = obtener_datos("SELECT id_usuario FROM usuarios WHERE usuario = ?", (usuario,))
                    if not check.empty:
                        st.error("❌ El nombre de usuario ya está en uso.")
                    else:
                        query = "INSERT INTO usuarios (nombre, rol, usuario, contrasena, salario, telefono) VALUES (?, 'Empleado', ?, ?, ?, ?)"
                        ejecutar_consulta(query, (nombre, usuario, clave, salario, telefono))
                        st.success(f"Empleado {nombre} registrado correctamente.")
                        time.sleep(1)
                        st.rerun()
                else:
                    st.warning("Complete los campos obligatorios (Nombre, Usuario y Clave).")

        st.divider()

        # Edición y eliminación
        with st.expander("🛠️ EDITAR O ELIMINAR TRABAJADORES"):
            id_edit = st.number_input("ID del Trabajador", min_value=1, step=1, key="id_worker_edit")
            emp_data = obtener_datos("SELECT * FROM usuarios WHERE id_usuario = ? AND rol = 'Empleado'", (id_edit,))
            
            if not emp_data.empty:
                with st.form("edit_worker_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1: nuevo_nom = st.text_input("Nombre", value=emp_data.iloc[0]['nombre'])
                    with c2: nuevo_sal = st.number_input("Salario", value=float(emp_data.iloc[0]['salario']))
                    with c3: nuevo_tel = st.text_input("Teléfono", value=emp_data.iloc[0]['telefono'])
                    
                    col_b1, col_b2 = st.columns(2)
                    if col_b1.form_submit_button("💾 Actualizar Datos", use_container_width=True):
                        ejecutar_consulta("UPDATE usuarios SET nombre=?, salario=?, telefono=? WHERE id_usuario=?", (nuevo_nom, nuevo_sal, nuevo_tel, id_edit))
                        st.success("Cambios guardados."); time.sleep(1); st.rerun()
                    
                    if col_b2.form_submit_button("🗑️ Dar de Baja", type="primary", use_container_width=True):
                        ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=?", (id_edit,))
                        st.warning("Trabajador eliminado."); time.sleep(1); st.rerun()
            else:
                st.caption("Ingrese un ID de empleado válido para editar.")

        st.write("### Nómina de Personal")
        df_users = obtener_datos("SELECT id_usuario as ID, nombre, usuario, salario as 'Salario (Bs)', telefono FROM usuarios WHERE rol = 'Empleado'")
        st.dataframe(df_users, use_container_width=True, hide_index=True)

    # --- 2. PESTAÑA: CONTROL DE ASISTENCIA ---
    with tab_asistencia:
        render_asistencia_logic()

def render_asistencia_logic():
    st.subheader("🕒 Reporte Semanal de Asistencia")
    
    turno_ver = st.radio("Seleccionar Turno para Reporte:", ["Mañana (08:30)", "Tarde (14:00)"], horizontal=True)
    
    # Configuración de límites según el turno
    if "Mañana" in turno_ver:
        rango_ini, rango_fin, hora_limite = "06:00:00", "13:00:00", "08:31"
    else:
        rango_ini, rango_fin, hora_limite = "13:01:00", "19:00:00", "14:01"

    query_turnos = f"""
        SELECT 
            nombre_usuario as Empleado,
            MIN(CASE WHEN strftime('%w', fecha_hora) = '1' THEN strftime('%H:%M', fecha_hora) END) as Lunes,
            MIN(CASE WHEN strftime('%w', fecha_hora) = '2' THEN strftime('%H:%M', fecha_hora) END) as Martes,
            MIN(CASE WHEN strftime('%w', fecha_hora) = '3' THEN strftime('%H:%M', fecha_hora) END) as Miercoles,
            MIN(CASE WHEN strftime('%w', fecha_hora) = '4' THEN strftime('%H:%M', fecha_hora) END) as Jueves,
            MIN(CASE WHEN strftime('%w', fecha_hora) = '5' THEN strftime('%H:%M', fecha_hora) END) as Viernes,
            MIN(CASE WHEN strftime('%w', fecha_hora) = '6' THEN strftime('%H:%M', fecha_hora) END) as Sabado
        FROM registro_accesos
        WHERE nombre_usuario NOT IN (SELECT nombre FROM usuarios WHERE rol = 'Jefe')
        AND TIME(fecha_hora) BETWEEN '{rango_ini}' AND '{rango_fin}'
        GROUP BY nombre_usuario, strftime('%W', fecha_hora)
        ORDER BY Empleado ASC
    """
    
    df_turno = obtener_datos(query_turnos).fillna("-")

    if not df_turno.empty:
        # Estilo para resaltar atrasos en rojo
        def resaltar_atrasos(val):
            if val != "-" and val > hora_limite:
                return 'color: red; font-weight: bold'
            return ''

        st.write(f"### Visualización: {turno_ver}")
        st.dataframe(df_turno.style.applymap(resaltar_atrasos, subset=['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado']), use_container_width=True)
        
        # Generación de PDF
        if st.button(f"📥 Exportar PDF {turno_ver}"):
            pdf = FPDF(orientation='L')
            pdf.add_page()
            if os.path.exists("logo.png"):
                pdf.image("logo.png", x=10, y=8, w=20)
            
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, txt=f"ASISTENCIA - {turno_ver.upper()}", ln=True, align='C')
            pdf.ln(10)
            
            # Encabezados
            pdf.set_font("Arial", 'B', 10)
            pdf.set_fill_color(230, 230, 230)
            cols = ["Empleado", "Lun", "Mar", "Mie", "Jue", "Vie", "Sab"]
            widths = [60, 35, 35, 35, 35, 35, 35]
            for i in range(len(cols)):
                pdf.cell(widths[i], 10, cols[i], 1, 0, 'C', True)
            pdf.ln()

            # Filas
            pdf.set_font("Arial", size=10)
            for _, row in df_turno.iterrows():
                pdf.set_text_color(0, 0, 0)
                pdf.cell(60, 10, str(row['Empleado']), 1)
                for dia in ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado']:
                    hora = str(row[dia])
                    if hora != "-" and hora > hora_limite:
                        pdf.set_text_color(255, 0, 0) # Rojo para atrasos
                    else:
                        pdf.set_text_color(0, 0, 0)
                    pdf.cell(35, 10, hora, 1, 0, 'C')
                pdf.ln()
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='replace')
            st.download_button(label="💾 Descargar Reporte", data=pdf_bytes, file_name=f"asistencia_{turno_ver}.pdf", mime="application/pdf")
    else:
        st.info(f"No hay registros de entrada para el turno {turno_ver}.")