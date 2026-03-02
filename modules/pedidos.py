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
    # Traemos linea y color para que el usuario sepa exactamente qué vende
    query_inv = "SELECT id, linea, nombre, color, cantidad, precio_venta FROM inventario WHERE cantidad > 0 ORDER BY linea, nombre ASC"
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
            
            # Selección de Producto con detalle completo (Línea + Nombre + Color)
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
            # Mostramos el precio sugerido del inventario como ayuda
            st.caption(f"Precio sugerido en inventario: {precio_sugerido} Bs")
            precio_total = st.number_input("Precio Total de la Venta (Bs)", min_value=0.0, format="%.2f")
            detalle_venta = st.text_area("Notas (Ej: Entregado en local, pendiente pago)")

        if st.form_submit_button("🚀 Confirmar Venta y Descontar Stock", use_container_width=True):
            if cantidad_pedida > stock_actual:
                st.error(f"❌ Stock insuficiente. Solo quedan {stock_actual} docenas de este color.")
            elif cantidad_pedida <= 0:
                st.warning("⚠️ La cantidad debe ser mayor a cero.")
            else:
                try:
                    # Ajuste de hora (Bolivia UTC-4)
                    fecha_bolivia = datetime.utcnow() - timedelta(hours=4)
                    fecha_str = fecha_bolivia.strftime("%Y-%m-%d %H:%M:%S")

                    # A. Insertar el Pedido
                    query_ins = """
                        INSERT INTO pedidos (id_cliente, id_inventario, cantidad, detalle, precio, fecha) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    ejecutar_consulta(query_ins, (id_cliente, id_inventario, cantidad_pedida, detalle_venta, precio_total, fecha_str))
                    
                    # B. Descontar del Inventario (usando el ID único)
                    ejecutar_consulta("UPDATE inventario SET cantidad = cantidad - %s WHERE id = %s", (cantidad_pedida, id_inventario))
                    
                    # C. Registro en Log
                    registrar_log(
                        accion="VENTA",
                        tabla="pedidos/inventario",
                        detalle=f"Venta: {cantidad_pedida} doc. de '{prod_info['nombre']} {prod_info['color']}' a '{cliente_sel}' por {precio_total} Bs."
                    )
                    
                    st.balloons()
                    st.success(f"✅ Venta exitosa registrada a las {fecha_bolivia.strftime('%H:%M')}")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error técnico al registrar la venta: {e}")

    # 2. Historial de Ventas (Añadimos Color y Línea para claridad)
    st.divider()
    st.subheader("📋 Últimas Ventas Realizadas")
    
    query_historial = """
        SELECT 
            p.id_pedido as "Nro", 
            c.nombre as "Cliente", 
            i.linea as "Línea",
            i.nombre as "Producto", 
            i.color as "Color",
            p.cantidad as "Cant", 
            p.precio as "Total (Bs)", 
            TO_CHAR(p.fecha, 'DD/MM HH24:MI') as "Fecha"
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        ORDER BY p.id_pedido DESC LIMIT 15
    """
    hist_df = obtener_datos(query_historial)
    if not hist_df.empty:
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay ventas registradas en el historial.")