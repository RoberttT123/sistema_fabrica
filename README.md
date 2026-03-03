# 🏭 Sistema de Gestión de Fábrica (Medias)

Este es un sistema integral desarrollado en **Python** y **Streamlit** para la gestión de inventario, ventas y control de asistencia de personal en una fábrica de medias. El sistema está diseñado para funcionar en un localHost o con la url que te ofrecee streamlit al momento de crear la app, permitiendo que los empleados registren su asistencia desde sus propios dispositivos.

## 🚀 Características Principales

* **🔐 Seguridad por Roles**: Acceso diferenciado para el **Jefe** (administración total) y **Empleados** (solo registro de asistencia).
* **🕒 Control de Asistencia Inteligente**: 
    * Registro automático por turnos (Mañana y Tarde).
    * Generación de reportes.
* **🧦 Gestión de Inventario**: Registro de productos con detalle, color y cantidad.
* **📊 Dashboard de Ventas**: Visualización de pedidos y estadísticas de comercialización.
* **📱 Acceso Local**: Servidor local accesible vía dirección IP (`http://XXX.XXX.XXX.XXX:XXXX`).

## 🛠️ Tecnologías Utilizadas

* **Frontend/App**: [Streamlit](https://streamlit.io/)
* **Base de Datos**: SQLite3
* **Lenguaje**: Python 3.10+
* **Reportes**: FPDF

## 📦 Instalación y Configuración

1. **Clonar el repositorio**:
   ```bash
   git clone [https://github.com/RoberttT123/sistema_fabrica.git](https://github.com/RoberttT123/sistema_fabrica.git)
   cd sistema_fabrica
