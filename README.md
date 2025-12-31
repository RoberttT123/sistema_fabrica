# 🏭 Sistema de Gestión de Fábrica (Medias)

Este es un sistema integral desarrollado en **Python** y **Streamlit** para la gestión de inventario, ventas y control de asistencia de personal en una fábrica de medias. El sistema está diseñado para funcionar en una red local (WiFi), permitiendo que los empleados registren su asistencia desde sus propios dispositivos.

## 🚀 Características Principales

* **🔐 Seguridad por Roles**: Acceso diferenciado para el **Jefe** (administración total) y **Empleados** (solo registro de asistencia).
* **🕒 Control de Asistencia Inteligente**: 
    * Registro automático por turnos (Mañana y Tarde).
    * Evita duplicidad de marcas (solo guarda la primera entrada de cada turno).
    * Generación de reportes semanales en **PDF** con resaltado de atrasos en rojo (Entradas después de las 08:31 AM y 14:01 PM).
* **🧦 Gestión de Inventario**: Registro de productos con detalle, color y cantidad, evitando valores nulos (`None`).
* **📊 Dashboard de Ventas**: Visualización de pedidos y estadísticas de comercialización.
* **📱 Acceso Local**: Servidor local accesible vía dirección IP (`http://192.168.12.139:8501`).

## 🛠️ Tecnologías Utilizadas

* **Frontend/App**: [Streamlit](https://streamlit.io/)
* **Base de Datos**: SQLite3
* **Lenguaje**: Python 3.10+
* **Reportes**: FPDF

## 📦 Instalación y Configuración

Sigue estos pasos para replicar el entorno en tu computadora:

1. **Clonar el repositorio**:
   ```bash
   git clone [https://github.com/TU_USUARIO/sistema_fabrica.git](https://github.com/TU_USUARIO/sistema_fabrica.git)
   cd sistema_fabrica
