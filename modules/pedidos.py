import streamlit as st
import time
from modules.database import ejecutar_consulta, obtener_datos

def realizar_pedido():
    st.header("🛒 Registro de Pedidos (Ventas)")

    # --- CALCULADORA INTELIGENTE DE UN SOLO CAMPO ---
    with st.expander("🧮 Calculadora Rápida (Escribe ej: 10*5)", expanded=True):
        operacion_input = st.text_input("Escribe tu operación aquí (usa +, -, *, /)", placeholder="Ejemplo: 50 * 3 + 10")
        
        if operacion_input:
            try:
                # Limpiamos el texto para seguridad (solo permitimos números y operadores)
                caracteres_validos = "0123456789+-*/. "
                if all(char in caracteres_validos for char in operacion_input):
                    # Calculamos el resultado
                    resultado_calc = eval(operacion_input)
                    st.metric("Resultado", f"{resultado_calc:.2f} Bs")
                    st.caption("💡 Puedes copiar este valor en el campo 'Precio Total' de abajo.")
                else:
                    st.warning("⚠️ Por favor, usa solo números y los símbolos +, -, *, /")
            except Exception:
                st.error("❌ Operación no válida. Revisa los signos.")

    # 1. Obtener datos con verificación de existencia
    clientes_df = obtener_datos("SELECT id_cliente, nombre FROM clientes")
    inventario_df = obtener_datos("SELECT id, nombre, color, cantidad FROM inventario WHERE cantidad > 0")

    if clientes_df.empty:
        st.warning("⚠️ No hay clientes registrados.")
        return

    if inventario_df.empty:
        st.info("📦 No hay stock disponible en el inventario.")
        return

    # --- FORMULARIO DE PEDIDO ---
    with st.form("form_pedido_inventario"):
        st.subheader("Nuevo Pedido")
        col1, col2 = st.columns(2)
        
        with col1:
            cliente_sel = st.selectbox("Seleccione al Cliente", clientes_df['nombre'].tolist())
            id_cliente = int(clientes_df[clientes_df['nombre'] == cliente_sel]['id_cliente'].values[0])
            
            opciones_inv = inventario_df.apply(lambda x: f"{x['id']} | {x['nombre']} - {x['color']} (Stock: {int(x['cantidad'])})", axis=1).tolist()
            producto_sel = st.selectbox("Seleccione el Producto", opciones_inv)
            
            id_inventario = int(producto_sel.split("|")[0].strip())
            stock_actual = inventario_df[inventario_df['id'] == id_inventario]['cantidad'].values[0]

        with col2:
            cantidad_pedida = st.number_input("Cantidad a vender", min_value=1, step=1)
            # Israel ingresa el resultado aquí
            precio_total = st.number_input("Precio Total (Bs)", min_value=0.0, format="%.2f")
            detalle_venta = st.text_area("Notas adicionales")

        if st.form_submit_button("🚀 Confirmar Venta"):
            if cantidad_pedida > stock_actual:
                st.error(f"❌ Stock insuficiente. Solo quedan {int(stock_actual)}.")
            else:
                try:
                    query_ins = """INSERT INTO pedidos (id_cliente, id_inventario, cantidad, detalle, precio, fecha) 
                                   VALUES (?, ?, ?, ?, ?, datetime('now'))"""
                    ejecutar_consulta(query_ins, (id_cliente, id_inventario, cantidad_pedida, detalle_venta, precio_total))
                    
                    ejecutar_consulta("UPDATE inventario SET cantidad = cantidad - ? WHERE id = ?", (cantidad_pedida, id_inventario))
                    
                    st.success("✅ Venta registrada exitosamente.")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error técnico: {e}")

    # 2. Historial de Ventas (con LEFT JOIN para evitar errores visuales)
    st.markdown("---")
    st.subheader("📋 Historial de Ventas")
    query_historial = """
        SELECT 
            p.id_pedido as 'Nro', 
            IFNULL(c.nombre, 'Desconocido') as Cliente, 
            IFNULL(i.nombre, 'Sin Detalle') as Detalle, 
            IFNULL(i.color, '-') as Color, 
            p.cantidad as Cant, 
            p.precio as Total, 
            p.fecha as Fecha
        FROM pedidos p
        LEFT JOIN clientes c ON p.id_cliente = c.id_cliente
        LEFT JOIN inventario i ON p.id_inventario = i.id
        ORDER BY p.id_pedido DESC
    """
    historial_df = obtener_datos(query_historial)
    if not historial_df.empty:
        st.dataframe(historial_df, use_container_width=True)
    else:
        st.info("Aún no hay ventas registradas.")