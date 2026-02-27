import streamlit as st
import time 
import pandas as pd
from datetime import datetime, timedelta  # <--- Agregamos timedelta
from modules.database import ejecutar_consulta, obtener_datos, registrar_log

def realizar_pedido():
    st.header("🛒 Registro de Pedidos (Ventas)")

    # --- CALCULADORA INTELIGENTE ---
    with st.expander("🧮 Calculadora de Precios", expanded=False):
        operacion_input = st.text_input("Escribe tu operación (ej: 12 * 110)", placeholder="Ejemplo: 50 * 3")
        if operacion_input:
            try:
                if all(c in "0123456789+-*/. " for c in operacion_input):
                    resultado_calc = eval(operacion_input)
                    st.success(f"Resultado: **{resultado_calc:.2f} Bs**")
                else:
                    st.warning("⚠️ Usa solo números y símbolos básicos.")
            except:
                st.error("❌ Operación no válida.")

    # 1. Obtener datos de la nube
    clientes_df = obtener_datos("SELECT id_cliente, nombre FROM clientes ORDER BY nombre ASC")
    inventario_df = obtener_datos("SELECT id, nombre, color, cantidad FROM inventario WHERE cantidad > 0 ORDER BY nombre ASC")

    if clientes_df.empty or inventario_df.empty:
        st.warning("⚠️ Asegúrate de tener Clientes e Inventario con stock en la nube.")
        return

    # --- FORMULARIO DE PEDIDO ---
    with st.form("form_pedido_inventario", clear_on_submit=True):
        st.subheader("Nuevo Pedido")
        col1, col2 = st.columns(2)
        
        with col1:
            cliente_sel = st.selectbox("Seleccione al Cliente", clientes_df['nombre'].tolist())
            id_cliente = int(clientes_df[clientes_df['nombre'] == cliente_sel]['id_cliente'].values[0])
            
            opciones_inv = inventario_df.apply(
                lambda x: f"{x['id']} | {x['nombre']} - {x['color']} (Stock: {int(x['cantidad'])})", axis=1
            ).tolist()
            producto_sel = st.selectbox("Seleccione el Producto", opciones_inv)
            
            id_inventario = int(producto_sel.split("|")[0].strip())
            nombre_producto = producto_sel.split("|")[1].split("(")[0].strip()
            stock_actual = inventario_df[inventario_df['id'] == id_inventario]['cantidad'].values[0]

        with col2:
            cantidad_pedida = st.number_input("Cantidad (Docenas)", min_value=1, step=1)
            precio_total = st.number_input("Precio Total (Bs)", min_value=0.0, format="%.2f", step=1.0)
            detalle_venta = st.text_area("Notas / Observaciones")

        if st.form_submit_button("🚀 Confirmar Venta en la Nube", use_container_width=True):
            if cantidad_pedida > stock_actual:
                st.error(f"❌ Stock insuficiente. Solo quedan {int(stock_actual)} docenas.")
            else:
                try:
                    # --- AJUSTE DE HORA BOLIVIA (Igual que en los logs) ---
                    # Usamos utcnow - 4 horas para asegurar precisión total
                    fecha_bolivia = datetime.utcnow() - timedelta(hours=4)
                    fecha_str = fecha_bolivia.strftime("%Y-%m-%d %H:%M:%S")

                    # A. Insertar Pedido usando la fecha calculada
                    query_ins = """
                        INSERT INTO pedidos (id_cliente, id_inventario, cantidad, detalle, precio, fecha) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    ejecutar_consulta(query_ins, (id_cliente, id_inventario, cantidad_pedida, detalle_venta, precio_total, fecha_str))
                    
                    # B. Actualizar Stock
                    ejecutar_consulta("UPDATE inventario SET cantidad = cantidad - %s WHERE id = %s", (cantidad_pedida, id_inventario))
                    
                    # C. REGISTRAR EN EL LOG DE AUDITORÍA
                    registrar_log(
                        accion="VENTA",
                        tabla="pedidos/inventario",
                        detalle=f"Vendió {cantidad_pedida} doc. de '{nombre_producto}' a '{cliente_sel}' por {precio_total} Bs."
                    )
                    
                    st.balloons()
                    st.success(f"✅ Venta registrada: {fecha_bolivia.strftime('%H:%M:%S')}")
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar: {e}")

    # 2. Historial rápido (Últimos 10 pedidos)
    st.divider()
    st.subheader("📋 Últimas Ventas")
    
    query_historial = """
        SELECT 
            p.id_pedido as "Nro", 
            COALESCE(c.nombre, 'Minorista') as "Cliente", 
            COALESCE(i.nombre, 'Producto') as "Producto", 
            p.cantidad as "Cant", 
            p.precio as "Total (Bs)", 
            TO_CHAR(p.fecha, 'DD/MM HH24:MI') as "Fecha"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        ORDER BY p.id_pedido DESC LIMIT 10
    """
    hist_df = obtener_datos(query_historial)
    if not hist_df.empty:
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("No se han registrado ventas recientemente.")