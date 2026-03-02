import streamlit as st
import pandas as pd
import time
from datetime import datetime
from modules.database import ejecutar_consulta, obtener_datos, registrar_log

def render_inventario():
    st.header("🧦 Inventario de Medias Terminadas")
    
    # 1. ESTRUCTURA DE PRODUCTOS
    ESTRUCTURA_PRODUCTOS = {
        "Lycra": ["Soporte Lycra", "Soporte Lycra delgado", "Pantalón Lycra delgado", "Panty grande", "Panty mediano (10-12)", "Panty pequeño (4-6)"],
        "Stretch": ["Soporte stretch", "Pantalón stretch", "Tobillera stretch"],
        "Lujo": ["Soporte lujo", "Pantalón lujo", "Tobillera lujo"],
        "Galochera": ["Estrella", "Menudo", "Dolar", "Doble rombo", "Mariposa"]
    }
    
    COLORES_GENERALES = sorted([
        "Romance", "Piel", "Coñac", "Tabaco", "Negro", "Blanco", 
        "Hueso blanco", "Hueso rosado", "Beige", "Dumbo", "Cartón", 
        "Acacia", "Calipso", "Chocolate", "Almendra", "Humo plata", 
        "Humo oscuro", "Uva", "Api", "Carbón", "Humo"
    ])

    tab_stock, tab_gestion = st.tabs(["📋 Stock en Bodega", "⚙️ Gestión de Inventario"])

    with tab_stock:
        st.subheader("Existencias Actuales")
        # Ajustado a las columnas reales de tu tabla
        query_stock = """
            SELECT 
                id as ID, 
                linea as Línea, 
                nombre as Detalle, 
                color as Color, 
                cantidad as Cantidad, 
                precio_venta as Precio, 
                fecha_actualizacion as "Última Carga" 
            FROM inventario 
            ORDER BY id DESC
        """
        df = obtener_datos(query_stock)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No hay registros aún en la base de datos.")

    with tab_gestion:
        st.subheader("➕ Registrar / Actualizar Producto")
        
        col_1, col_2, col_3 = st.columns(3)
        with col_1:
            linea_sel = st.selectbox("1. Seleccione Línea", list(ESTRUCTURA_PRODUCTOS.keys()))
        with col_2:
            tipo_sel = st.selectbox("2. Seleccione Tipo", ESTRUCTURA_PRODUCTOS[linea_sel])
        with col_3:
            color_sel = st.selectbox("3. Seleccione Color", COLORES_GENERALES)

        with st.form("form_nuevo_inv", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                cant = st.number_input("Cantidad a sumar (Docenas)", min_value=0.0, step=1.0)
            with col_b:
                precio = st.number_input("Nuevo Precio de Venta (Bs)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("🚀 Guardar en Supabase", use_container_width=True):
                # 1. Verificar si existe la combinación única (nombre + linea + color)
                query_check = "SELECT id, cantidad FROM inventario WHERE linea = %s AND nombre = %s AND color = %s"
                resultado = obtener_datos(query_check, (linea_sel, tipo_sel, color_sel))
                
                hora_registro = datetime.now()

                if not resultado.empty:
                    # 2. SI EXISTE: Actualizar cantidad y precio
                    id_existente = int(resultado.iloc[0]['id'])
                    nueva_cantidad = float(resultado.iloc[0]['cantidad'] or 0) + cant
                    
                    query_update = "UPDATE inventario SET cantidad = %s, precio_venta = %s, fecha_actualizacion = %s WHERE id = %s"
                    ejecutar_consulta(query_update, (nueva_cantidad, precio, hora_registro, id_existente))
                    registrar_log("UPDATE", "inventario", f"Actualizó ID {id_existente}: +{cant} doc. Total: {nueva_cantidad}")
                    st.success(f"✅ Stock actualizado: {tipo_sel} ({color_sel}). Total: {nueva_cantidad}")
                else:
                    # 3. SI NO EXISTE: Insertar (IMPORTANTE: No enviar ID para evitar errores de clave duplicada)
                    query_insert = """
                        INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    ejecutar_consulta(query_insert, (tipo_sel, linea_sel, tipo_sel, color_sel, cant, precio, hora_registro))
                    registrar_log("INSERT", "inventario", f"Nuevo: {tipo_sel} {color_sel} - Cant: {cant}")
                    st.success(f"✅ Nuevo registro: {tipo_sel} - {color_sel}")
                
                time.sleep(1)
                st.rerun()

        st.markdown("---")

        with st.expander("🛠️ MODIFICAR O ELIMINAR PRODUCTO"):
            id_sel = st.number_input("Ingrese ID del producto", min_value=1, step=1)
            datos = obtener_datos("SELECT * FROM inventario WHERE id = %s", (id_sel,))

            if not datos.empty:
                prod = datos.iloc[0]
                st.info(f"Editando ID {id_sel}: {prod['nombre']} ({prod['color']})")
                
                with st.form("form_edit_inv"):
                    e_col1, e_col2, e_col3 = st.columns(3)
                    with e_col1:
                        e_lin = st.selectbox("Línea", list(ESTRUCTURA_PRODUCTOS.keys()), index=list(ESTRUCTURA_PRODUCTOS.keys()).index(prod['linea']) if prod['linea'] in ESTRUCTURA_PRODUCTOS else 0)
                        e_tipo = st.selectbox("Tipo", ESTRUCTURA_PRODUCTOS[e_lin], index=ESTRUCTURA_PRODUCTOS[e_lin].index(prod['nombre']) if prod['nombre'] in ESTRUCTURA_PRODUCTOS[e_lin] else 0)
                    with e_col2:
                        e_col = st.selectbox("Color", COLORES_GENERALES, index=COLORES_GENERALES.index(prod['color']) if prod['color'] in COLORES_GENERALES else 0)
                        e_cant = st.number_input("Cantidad Total", value=float(prod['cantidad'] or 0.0))
                    with e_col3:
                        e_prec = st.number_input("Precio (Bs)", value=float(prod['precio_venta'] or 0.0))
                    
                    st.divider()
                    b1, b2, b3 = st.columns(3)
                    
                    if b1.form_submit_button("💾 Guardar"):
                        query_upd = """
                            UPDATE inventario 
                            SET linea=%s, nombre=%s, tamano=%s, color=%s, cantidad=%s, precio_venta=%s, fecha_actualizacion=%s 
                            WHERE id=%s
                        """
                        ejecutar_consulta(query_upd, (e_lin, e_tipo, e_tipo, e_col, e_cant, e_prec, datetime.now(), int(id_sel)))
                        registrar_log("UPDATE", "inventario", f"Edición manual ID {id_sel}")
                        st.success("Cambios guardados"); time.sleep(1); st.rerun()

                    if b2.form_submit_button("👯 Duplicar"):
                        query_ins = """
                            INSERT INTO inventario (nombre, linea, tamano, color, cantidad, precio_venta, fecha_actualizacion) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """
                        ejecutar_consulta(query_ins, (e_tipo, e_lin, e_tipo, e_col, e_cant, e_prec, datetime.now()))
                        st.success("Copia creada"); time.sleep(1); st.rerun()
                    
                    if st.session_state.rol == "Jefe":
                        if b3.form_submit_button("🗑️ Eliminar", type="primary"):
                            ejecutar_consulta("DELETE FROM inventario WHERE id=%s", (int(id_sel),))
                            registrar_log("DELETE", "inventario", f"Eliminó ID {id_sel}")
                            st.warning("Eliminado correctamente"); time.sleep(1); st.rerun()
                    else:
                        b3.button("🗑️ Eliminar", disabled=True, help="Acceso restringido")