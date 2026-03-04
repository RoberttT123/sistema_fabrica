import streamlit as st
import time 
import pandas as pd
from datetime import datetime, timedelta
from modules.database import ejecutar_consulta, obtener_datos, registrar_log

def realizar_pedido():
    st.header("🛒 Registro de Pedidos (Ventas)")

    # --- CALCULADORA INTELIGENTE ---
    with st.expander("🧮 Calculadora de Precios", expanded=False):
        operacion_input = st.text_input("Escribe tu operación (ej: 12 * 110)", placeholder="Ejemplo: 50 * 3")
        if operacion_input:
            try:
                # Evaluación segura de la operación matemática
                if all(c in "0123456789+-*/. " for c in operacion_input):
                    resultado_calc = eval(operacion_input)
                    st.success(f"Resultado: **{resultado_calc:.2f} Bs**")
                else:
                    st.warning("⚠️ Usa solo números y símbolos básicos.")
            except:
                st.error("❌ Operación no válida.")

    # 1. Obtener datos actualizados de Supabase
    clientes_df = obtener_datos("SELECT id_cliente, nombre FROM clientes ORDER BY nombre ASC")
    # Traemos todos los datos necesarios del inventario
    query_inv = "SELECT id, linea, nombre, tamano, color, cantidad, precio_venta FROM inventario WHERE cantidad > 0 ORDER BY linea, nombre ASC"
    inventario_df = obtener_datos(query_inv)

    if clientes_df.empty or inventario_df.empty:
        st.warning("⚠️ Se requiere tener Clientes e Inventario con stock disponible.")
        return

    # --- FORMULARIO DE PEDIDO ---
    with st.form("form_pedido_inventario", clear_on_submit=True):
        st.subheader("Registrar Nueva Venta")
        col1, col2 = st.columns(2)
        
        with col1:
            # Selección de Cliente
            cliente_sel = st.selectbox("Seleccione al Cliente", clientes_df['nombre'].tolist())
            id_cliente = int(clientes_df[clientes_df['nombre'] == cliente_sel]['id_cliente'].values[0])
            
            # Selección de Producto con detalle completo
            opciones_inv = inventario_df.apply(
                lambda x: f"{x['id']} | [{x['linea']}] {x['nombre']} - {x['color']} (Stock: {float(x['cantidad'])})", axis=1
            ).tolist()
            producto_sel = st.selectbox("Seleccione el Producto exacto", opciones_inv)
            
            # Extraer ID y datos del producto seleccionado
            id_inventario = int(producto_sel.split("|")[0].strip())
            prod_info = inventario_df[inventario_df['id'] == id_inventario].iloc[0]
            stock_actual = float(prod_info['cantidad'])
            precio_sugerido = float(prod_info['precio_venta'] or 0)

        with col2:
            cantidad_pedida = st.number_input("Cantidad a vender (Docenas)", min_value=0.1, step=1.0, format="%.1f")
            # El precio total se puede autocalcular si el usuario lo desea o ingresar manualmente
            st.caption(f"Precio sugerido: {precio_sugerido} Bs por docena")
            precio_total = st.number_input("Precio Total de la Venta (Bs)", min_value=0.0, format="%.2f")
            
            # Usamos el campo 'detalle' para guardar la descripción completa que pide el Excel
            detalle_auto = f"{prod_info['nombre']} {prod_info['linea']} {prod_info['color']}"
            detalle_venta = st.text_area("Detalle de la Venta / Notas", value=detalle_auto)

        if st.form_submit_button("🚀 Confirmar Venta y Descontar Stock", use_container_width=True):
            if cantidad_pedida > stock_actual:
                st.error(f"❌ Stock insuficiente. Solo quedan {stock_actual} docenas.")
            elif cantidad_pedida <= 0:
                st.warning("⚠️ La cantidad debe ser mayor a cero.")
            elif precio_total <= 0:
                st.warning("⚠️ El precio total debe ser mayor a cero.")
            else:
                try:
                    # Ajuste de hora (Bolivia UTC-4)
                    fecha_bolivia = datetime.utcnow() - timedelta(hours=4)
                    fecha_str = fecha_bolivia.strftime("%Y-%m-%d %H:%M:%S")

                    # A. Insertar el Pedido
                    # Nota: Usamos 'detalle' para guardar la descripción que luego saldrá en el reporte
                    query_ins = """
                        INSERT INTO pedidos (id_cliente, id_inventario, cantidad, detalle, precio, fecha) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    ejecutar_consulta(query_ins, (id_cliente, id_inventario, cantidad_pedida, detalle_venta, precio_total, fecha_str))
                    
                    # B. Descontar del Inventario
                    ejecutar_consulta("UPDATE inventario SET cantidad = cantidad - %s WHERE id = %s", (cantidad_pedida, id_inventario))
                    
                    # C. Registro en Log de Actividades
                    registrar_log(
                        accion="VENTA",
                        tabla="pedidos",
                        detalle=f"Venta de {cantidad_pedida} doc. de {prod_info['nombre']} a {cliente_sel} por {precio_total} Bs."
                    )
                    
                    st.balloons()
                    st.success(f"✅ Venta registrada correctamente para {cliente_sel}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar la venta: {e}")

    # --- 2. HISTORIAL DE VENTAS RECIENTES ---
    st.divider()
    st.subheader("📋 Últimas Ventas Realizadas")
    
    query_historial = """
        SELECT 
            p.id_pedido as "Nro", 
            TO_CHAR(p.fecha, 'DD/MM/YY HH24:MI') as "Fecha",
            c.nombre as "Cliente", 
            p.detalle as "Descripción",
            p.cantidad as "Cant. Doc", 
            p.precio as "Total Bs"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        ORDER BY p.id_pedido DESC LIMIT 15
    """
    hist_df = obtener_datos(query_historial)
    
    if not hist_df.empty:
        # Estilo para la tabla
        st.dataframe(
            hist_df, 
            use_container_width=True, 
            hide_index=True
        )
        
        # --- Botón para eliminar última venta en caso de error ---
        with st.expander("🗑️ Corregir error (Anular última venta)"):
            ultimo_id = int(hist_df.iloc[0]['Nro'])
            if st.button(f"Anular Pedido Nro {ultimo_id}", type="primary"):
                # 1. Obtener datos para devolver al inventario
                info_p = obtener_datos("SELECT id_inventario, cantidad FROM pedidos WHERE id_pedido = %s", (ultimo_id,))
                if not info_p.empty:
                    id_inv = int(info_p.iloc[0]['id_inventario'])
                    cant_p = float(info_p.iloc[0]['cantidad'])
                    # 2. Devolver stock
                    ejecutar_consulta("UPDATE inventario SET cantidad = cantidad + %s WHERE id = %s", (cant_p, id_inv))
                    # 3. Borrar pedido
                    ejecutar_consulta("DELETE FROM pedidos WHERE id_pedido = %s", (ultimo_id,))
                    st.warning("Pedido anulado y stock devuelto.")
                    time.sleep(1)
                    st.rerun()
    else:
        st.info("Aún no hay ventas registradas.")