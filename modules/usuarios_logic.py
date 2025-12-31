import time
import streamlit as st
from modules.database import ejecutar_consulta, obtener_datos
from datetime import datetime
import time

def gestionar_usuarios():
    st.header("👥 Gestión de Personal y Clientes")
    
    tab_empleados, tab_clientes, tab_asistencia = st.tabs([
        "👷 Gestión de Personal", 
        "🛍️ Cartera de Clientes", 
        "🕒 Registro de Accesos"
    ])

    # --- 1. PESTAÑA DE EMPLEADOS ---
    with tab_empleados:
        col_reg, col_edit = st.columns(2)
        
        with col_reg:
            st.subheader("Registrar Nuevo")
            with st.form("form_empleado", clear_on_submit=True):
                nombre = st.text_input("Nombre Completo")
                usuario = st.text_input("Usuario (Login)")
                clave = st.text_input("Contraseña", type="password")
                salario = st.number_input("Salario (Bs)", min_value=0.0)
                telefono = st.text_input("Teléfono")
                
                if st.form_submit_button("✅ Guardar"):
                    if nombre and usuario and clave:
                        check = obtener_datos("SELECT id_usuario FROM usuarios WHERE usuario = ?", (usuario,))
                        if not check.empty:
                            st.error("❌ El usuario ya existe.")
                        else:
                            query = "INSERT INTO usuarios (nombre, rol, usuario, contrasena, salario, telefono) VALUES (?, 'Empleado', ?, ?, ?, ?)"
                            ejecutar_consulta(query, (nombre, usuario, clave, salario, telefono))
                            st.success("Registrado.")
                            time.sleep(1)
                            st.rerun()

        with col_edit:
            st.subheader("Editar / Eliminar")
            id_edit = st.number_input("ID del Empleado", min_value=1, step=1, key="id_emp_edit")
            emp_data = obtener_datos("SELECT * FROM usuarios WHERE id_usuario = ?", (id_edit,))
            
            if not emp_data.empty:
                with st.form("edit_emp_form"):
                    nuevo_nom = st.text_input("Nombre", value=emp_data.iloc[0]['nombre'])
                    nuevo_sal = st.number_input("Salario", value=float(emp_data.iloc[0]['salario']))
                    nuevo_tel = st.text_input("Teléfono", value=emp_data.iloc[0]['telefono'])
                    
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("💾 Actualizar"):
                        query = "UPDATE usuarios SET nombre=?, salario=?, telefono=? WHERE id_usuario=?"
                        ejecutar_consulta(query, (nuevo_nom, nuevo_sal, nuevo_tel, id_edit))
                        st.success("Actualizado.")
                        time.sleep(1)
                        st.rerun()
                    
                    if c2.form_submit_button("🗑️ Eliminar"):
                        ejecutar_consulta("DELETE FROM usuarios WHERE id_usuario=?", (id_edit,))
                        st.warning("Eliminado.")
                        time.sleep(1)
                        st.rerun()
            else:
                st.info("Ingresa un ID válido para editar.")

        st.markdown("---")
        df_users = obtener_datos("SELECT id_usuario as ID, nombre, usuario, salario, telefono FROM usuarios WHERE rol = 'Empleado'")
        st.dataframe(df_users, use_container_width=True)

    # --- 2. PESTAÑA DE CLIENTES ---
    with tab_clientes:
        col_c_reg, col_c_edit = st.columns(2)
        
        with col_c_reg:
            st.subheader("Nuevo Cliente")
            with st.form("form_cli_reg", clear_on_submit=True):
                c_nom = st.text_input("Nombre / Razón Social")
                c_dir = st.text_input("Dirección")
                c_tel = st.text_input("Teléfono")
                c_ed = st.number_input("Edad", min_value=0, value=30)
                
                if st.form_submit_button("👤 Registrar"):
                    if c_nom:
                        ejecutar_consulta("INSERT INTO clientes (nombre, edad, direccion, telefono) VALUES (?,?,?,?)", (c_nom, c_ed, c_dir, c_tel))
                        st.success("Cliente Agregado.")
                        time.sleep(1)
                        st.rerun()

        with col_c_edit:
            st.subheader("Editar / Eliminar")
            id_cli = st.number_input("ID del Cliente", min_value=1, step=1, key="id_cli_edit")
            cli_data = obtener_datos("SELECT * FROM clientes WHERE id_cliente = ?", (id_cli,))
            
            if not cli_data.empty:
                with st.form("edit_cli_form"):
                    n_nom = st.text_input("Nombre", value=cli_data.iloc[0]['nombre'])
                    n_dir = st.text_input("Dirección", value=cli_data.iloc[0]['direccion'])
                    n_tel = st.text_input("Teléfono", value=cli_data.iloc[0]['telefono'])
                    n_ed = st.number_input("Edad", value=int(cli_data.iloc[0]['edad']))
                    
                    cc1, cc2 = st.columns(2)
                    if cc1.form_submit_button("💾 Guardar Cambios"):
                        ejecutar_consulta("UPDATE clientes SET nombre=?, direccion=?, telefono=?, edad=? WHERE id_cliente=?", (n_nom, n_dir, n_tel, n_ed, id_cli))
                        st.success("Cliente actualizado.")
                        time.sleep(1)
                        st.rerun()
                    
                    if cc2.form_submit_button("🗑️ Borrar Cliente"):
                        ejecutar_consulta("DELETE FROM clientes WHERE id_cliente=?", (id_cli,))
                        st.error("Cliente eliminado.")
                        time.sleep(1)
                        st.rerun()
            else:
                st.info("Busca un cliente por ID para editarlo.")

        st.markdown("---")
        df_cli = obtener_datos("SELECT id_cliente as ID, nombre, direccion, telefono, edad FROM clientes")
        st.dataframe(df_cli, use_container_width=True)

    # --- 3. PESTAÑA DE ASISTENCIA ---
    # --- 3. PESTAÑA DE ASISTENCIA ---
    with tab_asistencia:
        st.subheader("🕒 Control de Asistencia por Turnos")
        
        # Selector para ver Mañana o Tarde
        turno_ver = st.radio("Seleccionar Turno:", ["Mañana (Entrada 08:30)", "Tarde (Entrada 14:00)"], horizontal=True)
        
        # Definimos el rango horario según la elección
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
            # Función de resaltado dinámico según el turno seleccionado
            def resaltar_atrasos(val):
                if val != "-" and val > hora_limite:
                    return 'color: red; font-weight: bold'
                return ''

            st.write(f"### Reporte: {turno_ver}")
            st.dataframe(df_turno.style.applymap(resaltar_atrasos, subset=['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado']), use_container_width=True)
            
            # --- Generación de PDF (Ajustado para el turno actual) ---
            if st.button(f"📥 Descargar Reporte {turno_ver} (PDF)"):
                from fpdf import FPDF
                pdf = FPDF(orientation='L')
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, txt=f"REPORTE DE ASISTENCIA - {turno_ver.upper()}", ln=True, align='C')
                pdf.ln(10)
                
                # Encabezados
                pdf.set_fill_color(200, 220, 255)
                pdf.cell(50, 10, "Empleado", 1, 0, 'C', True)
                for dia in ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab"]:
                    pdf.cell(32, 10, dia, 1, 0, 'C', True)
                pdf.ln()

                # Filas con detección de atraso según el turno
                for _, row in df_turno.iterrows():
                    pdf.set_text_color(0, 0, 0)
                    pdf.cell(50, 10, str(row['Empleado']), 1)
                    for col in ['Lunes','Martes','Miercoles','Jueves','Viernes','Sabado']:
                        hora = str(row[col])
                        if hora != "-" and hora > hora_limite:
                            pdf.set_text_color(255, 0, 0)
                        else:
                            pdf.set_text_color(0, 0, 0)
                        pdf.cell(32, 10, hora, 1, 0, 'C')
                    pdf.ln()
                
                pdf_bytes = pdf_bytes = bytes(pdf.output())
                st.download_button("Click para descargar", pdf_bytes, f"asistencia_{turno_ver}.pdf")
        else:
            st.info(f"No hay registros para el {turno_ver} todavía.")