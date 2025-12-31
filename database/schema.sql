-- TABLA DE USUARIOS (Jefe y Empleados)
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('Jefe', 'Empleado')) NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,
    salario REAL,
    telefono TEXT
);

-- TABLA DE CLIENTES
CREATE TABLE IF NOT EXISTS clientes (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    edad INTEGER,
    direccion TEXT,
    telefono TEXT
);

-- TABLA DE FÁBRICA (Stock General/Productos)
CREATE TABLE IF NOT EXISTS fabrica (
    id_fabrica INTEGER PRIMARY KEY AUTOINCREMENT,
    detalle TEXT NOT NULL, -- Ej: Medias Cholita Algodón
    cantidad INTEGER DEFAULT 0
);

-- TABLA DE PEDIDOS
CREATE TABLE IF NOT EXISTS pedidos (
    id_pedido INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER,
    id_fabrica INTEGER,
    fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
    cantidad INTEGER,
    detalle TEXT,
    precio REAL,
    estado TEXT DEFAULT 'Pendiente',
    FOREIGN KEY (id_cliente) REFERENCES clientes(id_cliente),
    FOREIGN KEY (id_fabrica) REFERENCES fabrica(id_fabrica)
);