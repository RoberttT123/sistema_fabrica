import streamlit as st
import time
import os
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime

def gestionar_usuarios():
    st.header("👥 Gestión de Personal y Clientes")
    
    tab_empleados, tab_clientes, tab_asistencia = st.tabs([
        "👷 Gestión de Personal", 
        "🛍️ Cartera de Clientes", 
        "🕒 Registro de Accesos"
    ])

    # --- 1. PESTAÑA DE EMPLEADOS ---
    with tab_empleados:
        # 1.1 Registro (Siempre visible)
        st.subheader("Registrar Nuevo Empleado")
        with st.form("form_empleado", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                nombre = st.text_input("Nombre Completo")
                usuario = st.text_input("Usuario (Login)")
                clave = st.text_input("Contraseña", type="password")
            with col_b:
                salario = st.number_input("Salario (Bs)", min_value=0.0)
                telefono = st.text_input("Teléfono")
            
            if st.form_submit_button("✅ Guardar Empleado", use_container_width=True):
                if nombre and usuario and clave:
                    check = obtener_datos("SELECT id_usuario FROM usuarios WHERE usuario = ?", (usuario,))
                    if not check.empty:
                        st.error("❌ El usuario ya existe.")
                    else:
                        query = "INSERT INTO usuarios (nombre, rol, usuario, contrasena, salario, telefono) VALUES (?, 'Empleado', ?, ?, ?, ?)"
                        ejecutar_consulta(query, (nombre, usuario, clave, salario, telefono))
                        st.success("Registrado correctamente.")
                        time.sleep(1)
                        st.rerun()

        st.markdown("---")

        # 1.2 Edición/Eliminación (Oculto en Expander)
        with st.expander("🛠️ HAGA CLIC AQUÍ PARA EDITAR O ELIMINAR EMPLEADOS"):
            id_edit = st.number_input("ID del Empleado a buscar", min_value=1, step=1, key="id_emp_edit")
            emp_data = obtener_datos("SELECT * FROM usuarios WHERE id_usuario = ?", (id_edit,))
            
            if not emp_data.empty:
                st.info(f"Editando a: **{emp_data.iloc[0]['nombre']}**")
                with st.form("edit_emp_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        nuevo_nom = st.text_input("Nombre", value=emp_data.iloc[0]['nombre'])
                    with c2:
                        nuevo_sal = st.number_input("Salario", value=float(emp_data.iloc[0]['salario']))
                    with c3:
                        nuevo_tel = st.text_input("Teléfono", value=emp_data.iloc[0]['telefono'])
                    
                    col_btn_save, col_btn_del = st.columns(2)
                    if col_btn_save.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        query = "UPDATE usuarios SET nombre=?, salario=?, telefono=? WHERE id_usuario=?"
                        ejecutar_consulta(query, (nuevo_nom, nuevo_sal, nuevo_tel, id_edit))
                        st.success("Datos actualizados.")
                        time.sleep(1)
                        st.rerun()
                    
                    if col_btn_del.form_submit_button("🗑️ Eliminar Empleado", type="primary", use_container_width=True):
                        ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=?", (id_edit,))
                        st.warning("Empleado eliminado.")
                        time.sleep(1)
                        st.rerun()
            else:
                st.caption("Ingrese un ID válido para editar.")

        st.write("### Lista de Personal")
        df_users = obtener_datos("SELECT id_usuario as ID, nombre, usuario, salario, telefono FROM usuarios WHERE rol = 'Empleado'")
        st.dataframe(df_users, use_container_width=True)

    # --- 2. PESTAÑA DE CLIENTES ---
    with tab_clientes:
        # 2.1 Registro
        st.subheader("Registrar Nuevo Cliente")
        with st.form("form_cli_reg", clear_on_submit=True):
            col_ca, col_cb = st.columns(2)
            with col_ca:
                c_nom = st.text_input("Nombre / Razón Social")
                c_dir = st.text_input("Dirección")
            with col_cb:
                c_tel = st.text_input("Teléfono")
                c_ed = st.number_input("Edad", min_value=0, value=30)
            
            if st.form_submit_button("👤 Guardar Cliente", use_container_width=True):
                if c_nom:
                    ejecutar_consulta("INSERT INTO clientes (nombre, edad, direccion, telefono) VALUES (?,?,?,?)", (c_nom, c_ed, c_dir, c_tel))
                    st.success("Cliente Agregado.")
                    time.sleep(1)
                    st.rerun()

        st.markdown("---")

        # 2.2 Edición/Eliminación (Oculto en Expander)
        with st.expander("🛠️ HAGA CLIC AQUÍ PARA EDITAR O ELIMINAR CLIENTES"):
            id_cli = st.number_input("ID del Cliente a buscar", min_value=1, step=1, key="id_cli_edit")
            cli_data = obtener_datos("SELECT * FROM clientes WHERE id_cliente = ?", (id_cli,))
            
            if not cli_data.empty:
                st.info(f"Editando a: **{cli_data.iloc[0]['nombre']}**")
                with st.form("edit_cli_form"):
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        n_nom = st.text_input("Nombre", value=cli_data.iloc[0]['nombre'])
                        n_dir = st.text_input("Dirección", value=cli_data.iloc[0]['direccion'])
                    with cc2:
                        n_tel = st.text_input("Teléfono", value=cli_data.iloc[0]['telefono'])
                        n_ed = st.number_input("Edad", value=int(cli_data.iloc[0]['edad']))
                    
                    btn_c1, btn_c2 = st.columns(2)
                    if btn_c1.form_submit_button("💾 Guardar Cambios", use_container_width=True):
                        ejecutar_consulta("UPDATE clientes SET nombre=?, direccion=?, telefono=?, edad=? WHERE id_cliente=?", (n_nom, n_dir, n_tel, n_ed, id_cli))
                        st.success("Cliente actualizado.")
                        time.sleep(1)
                        st.rerun()
                    
                    if btn_c2.form_submit_button("🗑️ Borrar Cliente", type="primary", use_container_width=True):
                        ejecutar_consulta("DELETE FROM clientes WHERE id_cliente=?", (id_cli,))
                        st.error("Cliente eliminado.")
                        time.sleep(1)
                        st.rerun()
            else:
                st.caption("Ingrese un ID válido para editar.")

        st.write("### Cartera de Clientes")
        df_cli = obtener_datos("SELECT id_cliente as ID, nombre, direccion, telefono, edad FROM clientes")
        st.dataframe(df_cli, use_container_width=True)

    # --- 3. PESTAÑA DE ASISTENCIA ---
# --- 3. PESTAÑA DE ASISTENCIA ---
    with tab_asistencia:
        st.subheader("🕒 Control de Asistencia por Turnos")
        
        turno_ver = st.radio("Seleccionar Turno:", ["Mañana (Entrada 08:30)", "Tarde (Entrada 14:00)"], horizontal=True)
        
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
            def resaltar_atrasos(val):
                if val != "-" and val > hora_limite:
                    return 'color: red; font-weight: bold'
                return ''

            st.write(f"### Reporte: {turno_ver}")
            st.dataframe(df_turno.style.map(resaltar_atrasos, subset=['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado']), use_container_width=True)
            
            # --- LÓGICA DE GENERACIÓN DE PDF COMPLETA ---
            if st.button(f"📥 Generar PDF {turno_ver}"):
                from fpdf import FPDF
                
                pdf = FPDF(orientation='L') # Paisaje para que quepan los días
                pdf.add_page()
                
                # Logo
                if os.path.exists("logo.png"):
                    pdf.image("logo.png", x=10, y=8, w=20)
                
                # Título
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, txt=f"REPORTE DE ASISTENCIA - {turno_ver.upper()}", ln=True, align='C')
                pdf.ln(10)
                
                # Encabezados de Tabla
                pdf.set_font("Arial", 'B', 11)
                pdf.set_fill_color(200, 220, 255)
                pdf.cell(50, 10, "Empleado", 1, 0, 'C', True)
                for dia in ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab"]:
                    pdf.cell(35, 10, dia, 1, 0, 'C', True)
                pdf.ln()

                # Datos de los empleados
                pdf.set_font("Arial", size=10)
                for _, row in df_turno.iterrows():
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(50, 10, str(row['Empleado']), 1)
                    
                    for col in ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado']:
                        hora = str(row[col])
                        # Si hay atraso, pintar el texto de rojo en el PDF
                        if hora != "-" and hora > hora_limite:
                            pdf.set_text_color(255, 0, 0)
                        else:
                            pdf.set_text_color(0, 0, 0)
                        pdf.cell(35, 10, hora, 1, 0, 'C')
                    pdf.ln()
                
                # Solución al error de bytes/encoding
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                # Botón de descarga real que aparece tras generar
                st.download_button(
                    label="✅ Descargar Archivo PDF",
                    data=pdf_output,
                    file_name=f"asistencia_{turno_ver}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info(f"No hay registros para el {turno_ver} todavía.")