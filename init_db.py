import sqlite3

def inicializar_todo():
    # Conexión a la base de datos
    conn = sqlite3.connect('sistema_ventas.db')
    cursor = conn.cursor()

    print("🛠 Creando tablas del sistema...")

    # 1. Tabla de Usuarios (Jefe y Empleados)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        rol TEXT CHECK(rol IN ('Jefe', 'Empleado')) NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        contrasena TEXT NOT NULL,
        salario REAL,
        telefono TEXT
    )
    """)

    # 2. Tabla de Registro de Accesos (Control de Asistencia)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS registro_accesos (
        id_acceso INTEGER PRIMARY KEY AUTOINCREMENT,
        id_usuario INTEGER,
        nombre_usuario TEXT,
        fecha_hora DATETIME DEFAULT (datetime('now','localtime')),
        FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
    )
    """)

    # 3. Tabla de Clientes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        edad INTEGER,
        direccion TEXT,
        telefono TEXT
    )
    """)

    # 4. Tabla de Lotes (Producción)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lotes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_inicio DATETIME DEFAULT (datetime('now','localtime')),
        cantidad_docenas INTEGER NOT NULL,
        estado TEXT DEFAULT 'Crudo',
        color TEXT DEFAULT 'Blanco',
        id_cliente_asignado INTEGER,
        FOREIGN KEY (id_cliente_asignado) REFERENCES clientes(id_cliente)
    )
    """)

    # 5. Tabla de Inventario (Materia Prima e Importación)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        tipo TEXT CHECK(tipo IN ('Hilo', 'Repuesto')) NOT NULL,
        cantidad REAL DEFAULT 0,
        unidad_medida TEXT,
        fecha_actualizacion DATETIME DEFAULT (datetime('now','localtime'))
    )
    """)

    # 6. Tabla de Pedidos (Ventas)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
        id_cliente INTEGER,
        id_fabrica INTEGER,
        fecha DATETIME DEFAULT (datetime('now','localtime')),
        cantidad INTEGER,
        detalle TEXT,
        precio REAL,
        FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
        FOREIGN KEY (id_fabrica) REFERENCES lotes(id)
    )
    """)

    print("👤 Configurando usuario Administrador Maestro...")
    # Insertar al Jefe (Admin) por defecto
    cursor.execute("""
    INSERT OR IGNORE INTO usuarios (id_usuario, nombre, rol, usuario, contrasena, salario, telefono) 
    VALUES (1, 'Israel Administrador', 'Jefe', 'admin', '1234', 0, '70000000')
    """)

    conn.commit()
    conn.close()
    print("✅ ¡Base de datos inicializada correctamente!")

if __name__ == "__main__":
    inicializar_todo()