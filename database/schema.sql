-- 1. TABLA DE USUARIOS
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    rol TEXT CHECK(rol IN ('Jefe', 'Empleado')) NOT NULL,
    usuario TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,
    salario NUMERIC(10,2),
    telefono TEXT
);

-- 2. TABLA DE CLIENTES
CREATE TABLE clientes (
    id_cliente SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    edad INTEGER,
    direccion TEXT,
    telefono TEXT
);

-- 3. TABLA DE INVENTARIO
CREATE TABLE inventario (
    id SERIAL PRIMARY KEY,
    nombre TEXT,
    tipo TEXT,
    color TEXT,
    cantidad NUMERIC(10,2),
    unidad_medida TEXT,
    fecha_actualizacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    linea TEXT, 
    tamano TEXT, 
    precio_venta NUMERIC(10,2)
);

-- 4. TABLA DE LOTES
CREATE TABLE lotes (
    id SERIAL PRIMARY KEY,
    fecha_inicio TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cantidad_docenas INTEGER NOT NULL,
    estado TEXT DEFAULT 'Crudo',
    color TEXT DEFAULT 'Blanco',
    id_cliente_asignado INTEGER REFERENCES clientes(id_cliente)
);

-- 5. TABLA DE PEDIDOS
CREATE TABLE pedidos (
    id_pedido SERIAL PRIMARY KEY,
    id_cliente INTEGER REFERENCES clientes(id_cliente),
    id_fabrica INTEGER REFERENCES lotes(id), 
    fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cantidad INTEGER,
    detalle TEXT,
    precio NUMERIC(10,2), 
    id_inventario INTEGER REFERENCES inventario(id)
);

-- 6. TABLA DE PRODUCCIÓN EN CRUDO
CREATE TABLE produccion_crudo (
    id SERIAL PRIMARY KEY,
    fecha DATE DEFAULT CURRENT_DATE,
    n_maquina INTEGER NOT NULL,
    item TEXT NOT NULL,
    n_partidas INTEGER NOT NULL,
    docenas NUMERIC(10,2) NOT NULL
);

-- 7. TABLA DE MANTENIMIENTO
CREATE TABLE mantenimiento (
    id SERIAL PRIMARY KEY,
    fecha TEXT,
    n_maquina INTEGER,
    tipo TEXT,
    detalle TEXT,
    tecnico TEXT
);

-- 8. TABLA DE REGISTRO DE ACCESOS
CREATE TABLE registro_accesos (
    id_acceso SERIAL PRIMARY KEY,
    id_usuario INTEGER REFERENCES usuarios(id_usuario),
    nombre_usuario TEXT,
    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS log_actividades (
    id_log SERIAL PRIMARY KEY,
    id_usuario INT,
    nombre_usuario TEXT,
    accion TEXT,      
    tabla_afectada TEXT, 
    detalle TEXT,       
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);