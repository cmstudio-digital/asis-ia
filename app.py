import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime
import os

# ==========================================
# 1. CONFIGURACIÓN INICIAL Y ESTILOS SaaS
# ==========================================
st.set_page_config(
    page_title="Asis-IA | Tus Asistentes de IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stSidebar { background-color: #161b22; }
    div.stButton > button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #2ea043;
    }
    .banner-admin {
        padding: 10px; background-color: #1f6feb; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px;
    }
    .banner-trial {
        padding: 10px; background-color: #9e6a03; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px;
    }
    .badge-activo-mensual {
        padding: 8px; background-color: #1f883d; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px; font-size: 13px;
    }
    .badge-activo-anual {
        padding: 8px; background-color: #8957e5; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px; font-size: 13px;
    }
    .alerta-vencimiento-7 {
        padding: 10px; background-color: #b08800; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px; font-size: 13px;
    }
    .alerta-vencimiento-3 {
        padding: 10px; background-color: #bc4c00; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px; font-size: 13px;
    }
    .alerta-vencimiento-1 {
        padding: 10px; background-color: #da3633; color: white;
        border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 15px; font-size: 13px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CARGA DE DATOS DESDE GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=300)
def cargar_base_datos_usuarios():
    """
    Conecta con Google Sheets usando gspread y las credenciales de st.secrets
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        # Definimos los permisos necesarios para Google Sheets
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Cargamos las credenciales desde los secrets de Streamlit
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        
        # Autorizamos el cliente gspread
        gc = gspread.authorize(credentials)

        # Abre tu hoja de cálculo por su nombre (Asegúrate que se llame así en tu Google Drive o usa la URL)
        # Puedes cambiar "Asis-IA_DB" por el nombre exacto de tu archivo en Google Drive
        sh = gc.open("Asis-IA_DB") 
        
        # Selecciona la primera pestaña de la hoja
        worksheet = sh.get_worksheet(0)
        
        # Trae todos los registros a un DataFrame de Pandas
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df

    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        # Retorna un DataFrame vacío de respaldo si falla
        return pd.DataFrame()

df_usuarios = cargar_base_datos_usuarios()

# ==========================================
# 3. AUTENTICACIÓN, SEGURIDAD Y MEMORIA
# ==========================================
st.sidebar.title("🔐 Asis-IA Acceso")

if "correo_temp" not in st.session_state:
    st.session_state.correo_temp = ""

if "sesion_iniciada" not in st.session_state:
    st.session_state.sesion_iniciada = False

# Si la sesión NO está iniciada, mostramos el acceso
if not st.session_state.sesion_iniciada:
    if "correo_guardado" in st.session_state and st.session_state.correo_guardado and not st.session_state.correo_temp:
        st.session_state.correo_temp = st.session_state.correo_guardado

    # Usamos un formulario para que funcione tanto la tecla ENTER como el botón de abajo
    with st.sidebar.form(key='form_login'):
        correo_input = st.text_input("Ingresa tu correo electrónico registrado:", value=st.session_state.correo_temp).strip()
        submit_btn = st.form_submit_button(label="Entrar 🚀")

    if not correo_input or not submit_btn:
        st.markdown("## 🚀 Bienvenido a Asis-IA")
        st.info("Por favor, ingresa tu correo electrónico en la barra lateral, presiona **Enter** o haz clic en **Entrar** para acceder a tus asistentes.")
        st.stop()
    else:
        st.session_state.sesion_iniciada = True
        st.session_state.correo_temp = correo_input
        st.rerun()

correo_ingresado_previo = st.session_state.correo_temp

# Buscar al usuario
usuario_encontrado = df_usuarios[df_usuarios['correo'].str.lower() == correo_ingresado_previo.lower()]

if usuario_encontrado.empty:
    st.error("❌ Tu correo no se encuentra autorizado o registrado en el sistema.")
    st.stop()

# Extraer reglas maestras de seguridad desde Google Sheets
usuario_congelado = bool(usuario_encontrado.iloc[0].get('congelado', False))
usuario_autoguardado = bool(usuario_encontrado.iloc[0].get('autoguardado', True))

# Validar si la cuenta está congelada o pausada por seguridad
if usuario_congelado:
    st.error("🔒 Tu cuenta se encuentra temporalmente congelada o pausada por seguridad. Comunícate con el administrador para restaurar tu acceso.")
    st.stop()

# Gestionar memoria del navegador según la casilla de Google Sheets
if usuario_autoguardado:
    st.session_state.correo_guardado = correo_ingresado_previo
else:
    st.session_state.correo_guardado = ""

user_email = correo_ingresado_previo

# Buscar al usuario
usuario_encontrado = df_usuarios[df_usuarios['correo'].str.lower() == correo_ingresado_previo.lower()]

if usuario_encontrado.empty:
    st.error("❌ Tu correo no se encuentra autorizado o registrado en el sistema.")
    st.stop()

# Extraer reglas maestras de seguridad desde Google Sheets
usuario_congelado = bool(usuario_encontrado.iloc[0].get('congelado', False))
usuario_autoguardado = bool(usuario_encontrado.iloc[0].get('autoguardado', True))

# Validar si la cuenta está congelada o pausada por seguridad
if usuario_congelado:
    st.error("🔒 Tu cuenta se encuentra temporalmente congelada o pausada por seguridad. Comunícate con el administrador para restaurar tu acceso.")
    st.stop()

# Gestionar memoria del navegador según la casilla de Google Sheets
if "correo_guardado" not in st.session_state:
    st.session_state.correo_guardado = ""

if usuario_autoguardado:
    st.session_state.correo_guardado = correo_ingresado_previo
else:
    st.session_state.correo_guardado = "" # Limpia la memoria si desactivaste el autoguardado remotamente

user_email = correo_ingresado_previo
st.session_state.correo_temp = user_email

# Extraer rol y vigencia
user_rol = usuario_encontrado.iloc[0]['rol'].strip().lower()
fecha_act_str = str(usuario_encontrado.iloc[0]['fecha_activacion'])

try:
    fecha_act = datetime.strptime(fecha_act_str, "%Y-%m-%d %H:%M:%S")
except:
    fecha_act = datetime.strptime(fecha_act_str.split()[0], "%Y-%m-%d")

tiempo_transcurrido = datetime.now() - fecha_act
dias_transcurridos = tiempo_transcurrido.days

aviso_vencimiento_html = None

if user_rol != "admin" and user_rol != "pago_unico":
    if user_rol == "prueba":
        limite_dias = 7
        if dias_transcurridos >= limite_dias:
            st.error("⏳ Tu periodo de prueba gratuito de 7 días ha finalizado. Adquiere un plan para continuar.")
            st.stop()
        else:
            dias_restantes = limite_dias - dias_transcurridos
            if dias_restantes <= 1:
                aviso_vencimiento_html = '<div class="alerta-vencimiento-1">🚨 ¡Atención! Tu prueba vence hoy. ¡Renueva ahora!</div>'
            elif dias_restantes <= 3:
                aviso_vencimiento_html = f'<div class="alerta-vencimiento-3">⚠️ Tu prueba vence en {dias_restantes} días.</div>'
            elif dias_restantes <= 7:
                aviso_vencimiento_html = f'<div class="alerta-vencimiento-7">⭐ Tu prueba vence en {dias_restantes} días. ¡Aprovecha al máximo!</div>'

    elif user_rol == "activo_mensual":
        limite_dias = 30
        if dias_transcurridos >= limite_dias:
            st.error("⏳ Tu Plan Mensual ha expirado (más de 30 días). Por favor renueva tu suscripción.")
            st.stop()
        else:
            dias_restantes = limite_dias - dias_transcurridos
            if dias_restantes <= 1:
                aviso_vencimiento_html = '<div class="alerta-vencimiento-1">🚨 ¡Atención! Tu plan mensual vence hoy. ¡Renueva ya!</div>'
            elif dias_restantes <= 3:
                aviso_vencimiento_html = f'<div class="alerta-vencimiento-3">⚠️ Tu plan mensual vence en {dias_restantes} días.</div>'
            elif dias_restantes <= 7:
                aviso_vencimiento_html = f'<div class="alerta-vencimiento-7">💡 Tu plan mensual vence en {dias_restantes} días. ¡Prepárate para renovar!</div>'

    elif user_rol == "activo_anual":
        limite_dias = 365
        if dias_transcurridos >= limite_dias:
            st.error("⏳ Tu Plan Anual ha expirado (más de 365 días). Por favor renueva tu suscripción.")
            st.stop()
        else:
            dias_restantes = limite_dias - dias_transcurridos
            if dias_restantes <= 1:
                aviso_vencimiento_html = '<div class="alerta-vencimiento-1">🚨 ¡Atención! Tu plan anual vence hoy.</div>'
            elif dias_restantes <= 3:
                aviso_vencimiento_html = f'<div class="alerta-vencimiento-3">⚠️ Tu plan anual vence en {dias_restantes} días.</div>'
            elif dias_restantes <= 7:
                aviso_vencimiento_html = f'<div class="alerta-vencimiento-7">💎 Tu plan anual vence en {dias_restantes} días.</div>'

if user_rol == "admin":
    usuario_permisos = {
        "Asistente_Negocios_Estrategia": True,
        "Asistente_Ideas": True,
        "Asistente_Marketing": True,
        "Asistente_Finanzas": True,
    }
else:
    usuario_permisos = {
        "Asistente_Negocios_Estrategia": bool(usuario_encontrado.iloc[0].get('Asistente_Negocios_Estrategia', False)),
        "Asistente_Ideas": bool(usuario_encontrado.iloc[0].get('Asistente_Ideas', False)),
        "Asistente_Marketing": bool(usuario_encontrado.iloc[0].get('Asistente_Marketing', False)),
        "Asistente_Finanzas": bool(usuario_encontrado.iloc[0].get('Asistente_Finanzas', False)),
    }

# ==========================================
# 4. BANNERS Y DISTINTIVOS EN SIDEBAR
# ==========================================
st.sidebar.markdown("---")

if aviso_vencimiento_html:
    st.sidebar.markdown(aviso_vencimiento_html, unsafe_allow_html=True)

if user_rol == "admin":
    st.sidebar.markdown('<div class="banner-admin">👑 Administrador Maestro</div>', unsafe_allow_html=True)
elif user_rol == "prueba":
    st.sidebar.markdown('<div class="banner-trial">⭐ Estás en tu Prueba Gratuita</div>', unsafe_allow_html=True)
elif user_rol == "activo_mensual":
    st.sidebar.markdown('<div class="badge-activo-mensual">✅ Tu Cuenta: Plan Mensual Activo</div>', unsafe_allow_html=True)
elif user_rol == "activo_anual":
    st.sidebar.markdown('<div class="badge-activo-anual">💎 Tu Cuenta: Plan Anual Activo</div>', unsafe_allow_html=True)
elif user_rol == "pago_unico":
    st.sidebar.markdown('<div class="badge-activo-anual">⚡ Tu Cuenta: Acceso Vitalicio / Único</div>', unsafe_allow_html=True)

# ==========================================
# 5. FILTRAR ASISTENTES
# ==========================================
todos_los_asistentes = {
    "Asistente_Negocios_Estrategia": {
        "nombre": "💼 Consultor de Negocios y Estratega Digital",
        "prompt": "Eres un consultor experto en negocios y estratega digital. Ayudas a estructurar modelos de negocio y vender en internet."
    },
    "Asistente_Ideas": {
        "nombre": "💡 Generación de Ideas de Negocio",
        "prompt": "Eres un experto estratega de ideas y validación de emprendimientos desde cero."
    },
    "Asistente_Marketing": {
        "nombre": "📈 Marketing y Estrategia Digital",
        "prompt": "Eres un especialista en marketing digital, copywriting y pauta publicitaria."
    },
    "Asistente_Finanzas": {
        "nombre": "💰 Finanzas y Control de Caja",
        "prompt": "Eres un asesor financiero experto en optimización de presupuestos, costos y modelos de ingresos."
    }
}

asistentes_disponibles = {}
for key, info in todos_los_asistentes.items():
    if user_rol == "admin" or usuario_permisos.get(key, False):
        asistentes_disponibles[info["nombre"]] = info["prompt"]

if not asistentes_disponibles:
    st.sidebar.markdown("---")
    st.warning("⚠️ No tienes ningún asistente activo asignado en este momento.")
    st.stop()

# ==========================================
# 6. GESTIÓN DE CHATS Y MOTOR DE IA
# ==========================================
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Tus Asistentes Autorizados")

asistente_seleccionado = st.sidebar.selectbox("Selecciona un Asistente:", list(asistentes_disponibles.keys()))

if "chats_por_asistente" not in st.session_state:
    st.session_state.chats_por_asistente = {bot: {"Chat Principal": []} for bot in asistentes_disponibles.keys()}

for bot in asistentes_disponibles.keys():
    if bot not in st.session_state.chats_por_asistente:
        st.session_state.chats_por_asistente[bot] = {"Chat Principal": []}

if st.sidebar.button(f"➕ Nuevo chat para este asistente"):
    nuevo_nombre_chat = f"Chat {len(st.session_state.chats_por_asistente[asistente_seleccionado]) + 1} - {datetime.now().strftime('%H:%M')}"
    st.session_state.chats_por_asistente[asistente_seleccionado][nuevo_nombre_chat] = []
    st.rerun()

chats_disponibles_bot = list(st.session_state.chats_por_asistente[asistente_seleccionado].keys())
chat_activo = st.sidebar.selectbox("Selecciona una conversación:", chats_disponibles_bot)

try:
    from google import genai
    
    # Obtenemos la llave de los secrets o del entorno
    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY", "")
        
    # Inicializamos el cliente oficial
    client = genai.Client(api_key=api_key)
    
    # Definimos el modelo que siempre usas
    MODELO_SELECCIONADO = "gemini-3.5-flash"

except Exception as e:
    st.error(f"Error de configuración con la librería de Gemini: {e}")
    st.stop()

st.title(f"{asistente_seleccionado}")
st.markdown(f"<p style='font-size: 16px; color: #8b949e; margin-top: -10px; margin-bottom: 20px;'>{asistentes_disponibles[asistente_seleccionado]}</p>", unsafe_allow_html=True)

mensajes_actuales = st.session_state.chats_por_asistente[asistente_seleccionado][chat_activo]

for mensaje in mensajes_actuales:
    with st.chat_message(mensaje["role"]):
        st.markdown(mensaje["content"])

if prompt := st.chat_input("Escribe tu consulta aquí..."):
    mensajes_actuales.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt = asistentes_disponibles[asistente_seleccionado]
    full_prompt = f"{system_prompt}\n\nHistorial reciente y consulta del usuario:\n{prompt}"

    try:
        response = client.models.generate_content(
       model="gemini-3.5-flash",
       contents=full_prompt
   )
        respuesta_ia = response.text
    except Exception as e:
        respuesta_ia = f"Error técnico exacto: {e}"

    mensajes_actuales.append({"role": "assistant", "content": respuesta_ia})
    with st.chat_message("assistant"):
        st.markdown(respuesta_ia)

st.sidebar.markdown("---")
st.sidebar.subheader("📂 Gestión de Datos")

texto_historial_completo = ""
for m in mensajes_actuales:
    texto_historial_completo += f"{m['role'].upper()}: {m['content']}\n\n"

st.sidebar.download_button(
    label="📥 Descargar mi historial (.txt)",
    data=texto_historial_completo,
    file_name=f"historial_{asistente_seleccionado.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.txt",
    mime="text/plain"
)
st.sidebar.caption("💡 Tus chats se guardan por 30 días. Descarga tu documento antes de cambiar de dispositivo.")

# ==========================================
# 7. BOTÓN DE CERRAR SESIÓN
# ==========================================
st.sidebar.markdown("---")
if st.sidebar.button("🚪 Cerrar Sesión"):
    st.session_state.correo_temp = ""
    # NO borramos st.session_state.correo_guardado si el autoguardado está activo en Google Sheets
    # Así, al cerrar sesión, el correo se queda grabado para la próxima vez en su dispositivo.
    st.session_state.sesion_iniciada = False
    st.rerun()
