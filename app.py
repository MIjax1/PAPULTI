import streamlit as st
import sqlite3
import pandas as pd
import time
# Configuración de la página
st.set_page_config(page_title="Monitoreo de Pruebas PAP", layout="wide")

# Conectar a la base de datos
conn = sqlite3.connect("pap.db", check_same_thread=False)
cursor = conn.cursor()

# Crear tablas si no existen
cursor.execute("""
CREATE TABLE IF NOT EXISTS microredes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS establecimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE,
    microred_id INTEGER,
    FOREIGN KEY (microred_id) REFERENCES microredes(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    rol TEXT,
    establecimiento_id INTEGER,
    FOREIGN KEY (establecimiento_id) REFERENCES establecimientos(id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS pruebas_pap (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    edad INTEGER,
    fecha_toma DATE,
    fecha_entrega DATE,
    establecimiento_id INTEGER,
    estado TEXT DEFAULT 'pendiente',
    resultado TEXT,
    FOREIGN KEY (establecimiento_id) REFERENCES establecimientos(id)
)
""")

conn.commit()


# 📌 Insertar microredes si no existen
microredes = ["Acora", "Capachica", "Jose Antonio Encinas", "Laraqueri", "Mañazo", "Metropolitano", "Simon Bolivar"]

for microred in microredes:
    cursor.execute("SELECT id FROM microredes WHERE nombre = ?", (microred,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO microredes (nombre) VALUES (?)", (microred,))

conn.commit()

# 📌 Insertar establecimientos vinculados a microredes si no existen
establecimientos = [
    ("Establecimiento A", "Acora"),
    ("Establecimiento B", "Acora"),
    ("Establecimiento C", "Capachica"),
    ("Establecimiento D", "Capachica"),
    ("Establecimiento E", "Jose Antonio Encinas"),
    ("Establecimiento F", "Jose Antonio Encinas"),
    ("Establecimiento G", "Laraqueri"),
    ("Establecimiento H", "Mañazo"),
    ("Establecimiento I", "Metropolitano"),
    ("Establecimiento J", "Simon Bolivar")
]

for establecimiento, microred in establecimientos:
    cursor.execute("SELECT id FROM microredes WHERE nombre = ?", (microred,))
    microred_id = cursor.fetchone()
    
    if microred_id:
        microred_id = microred_id[0]
        cursor.execute("SELECT id FROM establecimientos WHERE nombre = ?", (establecimiento,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO establecimientos (nombre, microred_id) VALUES (?, ?)", (establecimiento, microred_id))

conn.commit()

# 📌 Insertar obstetras (usuarios) asegurando microred y establecimiento
usuarios = [
    ("obstetra1", "12345", "obstetra", "Establecimiento A"),
    ("obstetra2", "12345", "obstetra", "Establecimiento B"),
    ("obstetra3", "12345", "obstetra", "Establecimiento C"),
    ("obstetra4", "12345", "obstetra", "Establecimiento D"),
    ("obstetra5", "12345", "obstetra", "Establecimiento E"),
    ("obstetra6", "12345", "obstetra", "Establecimiento F"),
    ("obstetra7", "12345", "obstetra", "Establecimiento G"),
    ("obstetra8", "12345", "obstetra", "Establecimiento H"),
    ("obstetra9", "12345", "obstetra", "Establecimiento I"),
    ("obstetra10", "12345", "obstetra", "Establecimiento J"),
    ("jefe", "admin123", "jefe", None)  # Jefe con acceso global
]

for username, password, rol, establecimiento_nombre in usuarios:
    establecimiento_id = None
    if establecimiento_nombre:
        cursor.execute("SELECT id FROM establecimientos WHERE nombre = ?", (establecimiento_nombre,))
        result = cursor.fetchone()
        if result:
            establecimiento_id = result[0]

    cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
    if not cursor.fetchone():  # Verifica si el usuario ya existe
        cursor.execute("INSERT INTO usuarios (username, password, rol, establecimiento_id) VALUES (?, ?, ?, ?)",
                       (username, password, rol, establecimiento_id))

conn.commit()




# 📌 Función para autenticar usuarios
def autenticar_usuario(username, password):
    cursor.execute("SELECT id, rol, establecimiento_id FROM usuarios WHERE username = ? AND password = ?", (username, password))
    return cursor.fetchone()

# 📌 Función para obtener datos del establecimiento y microred
def obtener_info_establecimiento(establecimiento_id):
    cursor.execute("""
        SELECT e.nombre, m.nombre 
        FROM establecimientos e
        JOIN microredes m ON e.microred_id = m.id
        WHERE e.id = ?
    """, (establecimiento_id,))
    return cursor.fetchone()

# 📌 Función para obtener estadísticas del establecimiento
def obtener_estadisticas(establecimiento_id):
    cursor.execute("SELECT COUNT(*) FROM pruebas_pap WHERE establecimiento_id = ?", (establecimiento_id,))
    total_pacientes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pruebas_pap WHERE establecimiento_id = ? AND resultado = 'positivo'", (establecimiento_id,))
    positivos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pruebas_pap WHERE establecimiento_id = ? AND resultado = 'negativo'", (establecimiento_id,))
    negativos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pruebas_pap WHERE establecimiento_id = ? AND resultado IS NULL", (establecimiento_id,))
    sin_resultado = cursor.fetchone()[0]

    return total_pacientes, positivos, negativos, sin_resultado

if "usuario" not in st.session_state:
    st.session_state["usuario"] = None

# Si el usuario no está autenticado, muestra la pantalla de login
if st.session_state["usuario"] is None:
    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")
    
    if st.button("Iniciar sesión"):
        usuario = autenticar_usuario(username, password)
        if usuario:
            st.session_state["usuario"] = usuario
        else:
            st.error("Usuario o contraseña incorrectos")
else:
    # Si ya hay un usuario, muestra el contenido principal
    st.write("Bienvenido,", st.session_state["usuario"])

# 📌 Panel de Monitoreo
if "usuario" in st.session_state:
    usuario_id, rol, establecimiento_id = st.session_state.usuario
    
    # Obtener info del establecimiento y la microred
    if establecimiento_id:
        nombre_establecimiento, nombre_microred = obtener_info_establecimiento(establecimiento_id)
    else:
        nombre_establecimiento, nombre_microred = "Acceso Global", "Todas las Microredes"

    # 📌 Panel lateral izquierdo con información
    with st.sidebar:
        st.subheader("📌 Información")
        st.write(f"**Microred:** {nombre_microred}")
        st.write(f"**Establecimiento:** {nombre_establecimiento}")

        if establecimiento_id:
            total_pacientes, positivos, negativos, sin_resultado = obtener_estadisticas(establecimiento_id)
            st.subheader("📊 Estadísticas")
            st.write(f"📌 **Total Pacientes:** {total_pacientes}")
            st.write(f"✅ **Positivos:** {positivos}")
            st.write(f"❌ **Negativos:** {negativos}")
            st.write(f"⏳ **Sin Resultado:** {sin_resultado}")

    # 📌 Panel de obstetras
    if rol == "obstetra":
        st.header("Dashboard de Obstetra")

        # 📌 Formulario para registrar nueva prueba PAP
        with st.form("nueva_pap"):
            st.subheader("Registrar Nueva Prueba PAP")
            nombre = st.text_input("Nombre del Paciente")
            edad = st.number_input("Edad", min_value=10, max_value=100, step=1)
            fecha_toma = st.date_input("Fecha de Toma")
            fecha_entrega = st.date_input("Fecha de Entrega")
            submit_button = st.form_submit_button("Registrar")

            if submit_button:
                cursor.execute("""
                    INSERT INTO pruebas_pap (nombre, edad, fecha_toma, fecha_entrega, establecimiento_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (nombre, edad, fecha_toma, fecha_entrega, establecimiento_id))
                conn.commit()
                st.success("Prueba registrada correctamente")
                

        # 📌 Mostrar las pruebas de PAP del establecimiento de la obstetra
        st.subheader("Pacientes Registrados")
        cursor.execute("""
            SELECT id, nombre, edad, fecha_toma, fecha_entrega, estado, resultado
            FROM pruebas_pap
            WHERE establecimiento_id = ?
        """, (establecimiento_id,))
        datos = cursor.fetchall()
        df = pd.DataFrame(datos, columns=["ID", "Nombre", "Edad", "Fecha de Toma", "Fecha de Entrega", "Estado", "Resultado"])
        st.dataframe(df)

    # 📌 Panel del jefe
    elif rol == "jefe":
        st.header("Dashboard del Jefe")

        # 📌 Mostrar todas las pruebas PAP
        cursor.execute("""
            SELECT p.id, e.nombre AS Establecimiento, p.nombre, p.edad, p.fecha_toma, p.fecha_entrega, p.estado, p.resultado
            FROM pruebas_pap p
            JOIN establecimientos e ON p.establecimiento_id = e.id
        """)
        datos = cursor.fetchall()
        df = pd.DataFrame(datos, columns=["ID", "Establecimiento", "Nombre", "Edad", "Fecha de Toma", "Fecha de Entrega", "Estado", "Resultado"])
        
        # 📌 Permitir al jefe editar estado y resultado
        st.subheader("Modificar Pruebas PAP")
        prueba_id = st.number_input("ID de la Prueba a Modificar", min_value=1, step=1)
        
        # Opciones de estado y resultado
        nuevo_estado = st.selectbox("Nuevo Estado", ["pendiente", "en proceso", "completado"])
        nuevo_resultado = st.text_input("Nuevo Resultado")
        
        if st.button("Actualizar Prueba"):
            try:
                cursor.execute("""
                    UPDATE pruebas_pap
                    SET estado = ?, resultado = ?
                    WHERE id = ?
                """, (nuevo_estado, nuevo_resultado, prueba_id))
                conn.commit()
                st.success("Prueba actualizada correctamente")
                # Espera medio segundo para permitir que se muestre el mensaje
                time.sleep(0.5)
              
            except Exception as e:
                st.error("Error al actualizar la prueba: " + str(e))
        
        # 📌 Mostrar tabla con todas las pruebas
        st.subheader("Todas las Pruebas PAP")
        st.dataframe(df)
    if st.button("Cerrar sesión"):
        if "usuario" in st.session_state:
            del st.session_state["usuario"]
        

