from datetime import datetime
from storage import cargar_json, guardar_json
from config  import ADMINS, MODO_TEST, MENSAJES_FILE
from services import (
    generar_horarios, normalizar_hora,
    horario_bloqueado, bloquear_horario,
    obtener_turnos, guardar_turnos, turnos_usuario,
    horarios_libres, agregar_turno, cancelar_turno,
    guardar_mensaje,
)

# ── Clave de estado en storage ────────────────────────────────────────────────
ESTADO_KEY = "estados_usuarios"

# ── Menús ─────────────────────────────────────────────────────────────────────

MENU_PACIENTE = """🦙 E-Bot

1 Turno
2 Mis turnos
3 Mensaje
4 Urgencia
5 Informes
6 Salir"""

MENU_ADMIN = """🛠 ADMIN

1 Turnos hoy
2 Próximos turnos
3 Mensajes
4 Nuevo turno
5 Cancelar turno
6 Bloquear agenda
7 Salir"""


# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO
# ═══════════════════════════════════════════════════════════════════════════════

def get_estado():
    return cargar_json(ESTADO_KEY)

def save_estado(data):
    guardar_json(ESTADO_KEY, data)

def set_user_state(numero, key, value):
    estado = get_estado()
    estado.setdefault(numero, {})
    estado[numero][key] = value
    save_estado(estado)

def get_user_state(numero, key, default=None):
    return get_estado().get(numero, {}).get(key, default)

def clear_user(numero):
    estado = get_estado()
    estado[numero] = {}
    save_estado(estado)


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRADA PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def procesar(numero, body, resp):
    texto  = body.lower().strip()
    msg    = resp.message()
    estado = get_user_state(numero, "estado", "MENU")

    # ── ACCESO ADMIN ──────────────────────────────────────────────────────────

    if MODO_TEST and texto == "adm":
        set_user_state(numero, "estado", "ADMIN")
        msg.body(MENU_ADMIN)
        return

    if not MODO_TEST and numero in ADMINS and estado != "ADMIN":
        set_user_state(numero, "estado", "ADMIN")
        msg.body(MENU_ADMIN)
        return

    # ── RESET GLOBAL ─────────────────────────────────────────────────────────

    if texto in ["menu", "/start"]:
        clear_user(numero)
        msg.body(MENU_PACIENTE)
        return

    # ── ROUTER ───────────────────────────────────────────────────────────────

    if estado == "ADMIN":
        manejar_admin(numero, body, msg)
        return

    if estado == "MENSAJE":
        guardar_mensaje("Paciente", numero, body)
        msg.body("✅ Mensaje recibido")
        set_user_state(numero, "estado", "MENU")
        return

    if estado == "MENU":
        manejar_menu(numero, body, msg)
        return

    # ── FLUJO TURNO PACIENTE ─────────────────────────────────────────────────

    if estado == "TURNO_NOMBRE":
        set_user_state(numero, "nombre", body)
        set_user_state(numero, "estado", "TURNO_FECHA")
        msg.body("Ingresá la fecha del turno (dd/mm/yyyy)")
        return

    if estado == "TURNO_FECHA":
        _flujo_turno_fecha(numero, body, msg)
        return

    if estado == "TURNO_HORA":
        _flujo_turno_hora(numero, body, msg)
        return

    # ── FLUJO ADMIN ───────────────────────────────────────────────────────────

    if estado == "ADMIN_NUEVO_NOMBRE":
        set_user_state(numero, "adm_nombre", body)
        set_user_state(numero, "estado", "ADMIN_NUEVO_TEL")
        msg.body("Teléfono del paciente (whatsapp:+549XXXXXXXXXX)")
        return

    if estado == "ADMIN_NUEVO_TEL":
        set_user_state(numero, "adm_tel", body)
        set_user_state(numero, "estado", "ADMIN_NUEVO_FECHA")
        msg.body("Fecha del turno (dd/mm/yyyy)")
        return

    if estado == "ADMIN_NUEVO_FECHA":
        _flujo_admin_nuevo_fecha(numero, body, msg)
        return

    if estado == "ADMIN_NUEVO_HORA":
        _flujo_admin_nuevo_hora(numero, body, msg)
        return

    if estado == "ADMIN_CANCEL_FECHA":
        _flujo_admin_cancel_fecha(numero, body, msg)
        return

    if estado == "ADMIN_CANCEL_HORA":
        _flujo_admin_cancel_hora(numero, body, msg)
        return

    if estado == "BLOQUEAR_FECHA":
        _flujo_bloquear_fecha(numero, body, msg)
        return

    if estado == "BLOQUEAR_HORA":
        _flujo_bloquear_hora(numero, body, msg)
        return

    # ── FALLBACK ──────────────────────────────────────────────────────────────
    msg.body(MENU_PACIENTE)


# ═══════════════════════════════════════════════════════════════════════════════
# FLUJOS PACIENTE
# ═══════════════════════════════════════════════════════════════════════════════

def manejar_menu(numero, body, msg):
    opciones = {
        "1": _iniciar_turno,
        "2": _mis_turnos,
        "3": _iniciar_mensaje,
        "4": _urgencia,
        "5": _informes,
        "6": _salir,
    }
    accion = opciones.get(body.strip())
    if accion:
        accion(numero, msg)
    else:
        msg.body(MENU_PACIENTE)


def _iniciar_turno(numero, msg):
    set_user_state(numero, "estado", "TURNO_NOMBRE")
    msg.body("¿Cuál es tu nombre y apellido?")

def _mis_turnos(numero, msg):
    lista = turnos_usuario(numero)
    if not lista:
        msg.body("No tenés turnos próximos.")
    else:
        salida = "\n".join(f"📅 {t['fecha']} {t['hora']}" for t in lista)
        msg.body(salida)

def _iniciar_mensaje(numero, msg):
    set_user_state(numero, "estado", "MENSAJE")
    msg.body("Escribí tu mensaje y lo recibiremos a la brevedad.")

def _urgencia(numero, msg):
    msg.body("🚨 Urgencias: +549000000000")

def _informes(numero, msg):
    msg.body("🕘 Horario de atención: 09:00 a 19:00 hs")

def _salir(numero, msg):
    clear_user(numero)
    msg.body("Hasta luego 👋")


def _flujo_turno_fecha(numero, body, msg):
    try:
        fecha = datetime.strptime(body.strip(), "%d/%m/%Y").date()
    except ValueError:
        msg.body("❌ Formato inválido. Ingresá dd/mm/yyyy")
        return

    if fecha < datetime.now().date():
        msg.body("❌ La fecha ya pasó. Ingresá una fecha futura.")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    set_user_state(numero, "fecha", fecha_str)

    libres = horarios_libres(fecha_str)
    if not libres:
        msg.body("Sin horarios disponibles para esa fecha.")
        set_user_state(numero, "estado", "MENU")
        return

    set_user_state(numero, "estado", "TURNO_HORA")
    msg.body("Horarios disponibles:\n" + "\n".join(libres))


def _flujo_turno_hora(numero, body, msg):
    hora = normalizar_hora(body)
    if hora is None or hora not in generar_horarios():
        msg.body("❌ Hora inválida. Elegí un horario de la lista.")
        return

    fecha = get_user_state(numero, "fecha")

    if horario_bloqueado(fecha, hora):
        msg.body("❌ Ese horario está bloqueado.")
        return

    turnos = obtener_turnos()
    if any(t["fecha"] == fecha and t["hora"] == hora for t in turnos):
        msg.body("❌ Ese horario ya está ocupado. Elegí otro.")
        return

    nombre = get_user_state(numero, "nombre")
    agregar_turno(nombre, numero, fecha, hora)
    msg.body(f"✅ Turno confirmado\n📅 {fecha} a las {hora} hs\nNombre: {nombre}")
    clear_user(numero)


# ═══════════════════════════════════════════════════════════════════════════════
# FLUJOS ADMIN
# ═══════════════════════════════════════════════════════════════════════════════

def manejar_admin(numero, body, msg):
    turnos = obtener_turnos()

    if body == "1":
        hoy   = datetime.now().strftime("%d/%m/%Y")
        lista = [t for t in turnos if t["fecha"] == hoy]
        if not lista:
            msg.body("Sin turnos para hoy.")
        else:
            msg.body("📋 Turnos de hoy:\n" + "\n".join(
                f"{t['hora']} — {t['nombre']}" for t in sorted(lista, key=lambda x: x["hora"])
            ))
        return

    if body == "2":
        hoy     = datetime.now().date()
        futuros = [
            t for t in turnos
            if datetime.strptime(t["fecha"], "%d/%m/%Y").date() >= hoy
        ]
        futuros.sort(key=lambda x: (x["fecha"], x["hora"]))
        if not futuros:
            msg.body("Sin turnos próximos.")
        else:
            msg.body("📋 Próximos turnos:\n" + "\n".join(
                f"{t['fecha']} {t['hora']} — {t['nombre']}" for t in futuros
            ))
        return

    if body == "3":
        mensajes = cargar_json(MENSAJES_FILE).get("data", [])
        if not mensajes:
            msg.body("Sin mensajes.")
        else:
            msg.body("📨 Mensajes:\n" + "\n".join(
                f"{m['nombre']} ({m['telefono']}): {m['mensaje']}" for m in mensajes
            ))
        return

    if body == "4":
        set_user_state(numero, "estado", "ADMIN_NUEVO_NOMBRE")
        msg.body("Nombre del paciente")
        return

    if body == "5":
        set_user_state(numero, "estado", "ADMIN_CANCEL_FECHA")
        msg.body("Fecha del turno a cancelar (dd/mm/yyyy)")
        return

    if body == "6":
        set_user_state(numero, "estado", "BLOQUEAR_FECHA")
        msg.body("Fecha a bloquear (dd/mm/yyyy)")
        return

    if body == "7":
        clear_user(numero)
        msg.body("Salida del panel admin 👋")
        return

    msg.body(MENU_ADMIN)


def _flujo_admin_nuevo_fecha(numero, body, msg):
    try:
        fecha = datetime.strptime(body.strip(), "%d/%m/%Y").date()
    except ValueError:
        msg.body("❌ Formato inválido. Ingresá dd/mm/yyyy")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    set_user_state(numero, "adm_fecha", fecha_str)

    libres = horarios_libres(fecha_str)
    if not libres:
        msg.body("Sin horarios disponibles para esa fecha.")
        set_user_state(numero, "estado", "ADMIN")
        return

    set_user_state(numero, "estado", "ADMIN_NUEVO_HORA")
    msg.body("Horarios disponibles:\n" + "\n".join(libres))


def _flujo_admin_nuevo_hora(numero, body, msg):
    hora = normalizar_hora(body)
    if hora is None or hora not in generar_horarios():
        msg.body("❌ Hora inválida.")
        return

    fecha  = get_user_state(numero, "adm_fecha")
    nombre = get_user_state(numero, "adm_nombre")
    tel    = get_user_state(numero, "adm_tel")

    if horario_bloqueado(fecha, hora):
        msg.body("❌ Ese horario está bloqueado.")
        return

    turnos = obtener_turnos()
    if any(t["fecha"] == fecha and t["hora"] == hora for t in turnos):
        msg.body("❌ Ese horario ya está ocupado.")
        return

    agregar_turno(nombre, tel, fecha, hora)
    msg.body(f"✅ Turno creado\n{fecha} {hora} — {nombre}")
    set_user_state(numero, "estado", "ADMIN")


def _flujo_admin_cancel_fecha(numero, body, msg):
    try:
        fecha = datetime.strptime(body.strip(), "%d/%m/%Y").date()
    except ValueError:
        msg.body("❌ Formato inválido. Ingresá dd/mm/yyyy")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    turnos    = obtener_turnos()
    del_dia   = [t for t in turnos if t["fecha"] == fecha_str]

    if not del_dia:
        msg.body("No hay turnos en esa fecha.")
        set_user_state(numero, "estado", "ADMIN")
        return

    set_user_state(numero, "adm_cancel_fecha", fecha_str)
    set_user_state(numero, "estado", "ADMIN_CANCEL_HORA")
    msg.body("Turnos del día:\n" + "\n".join(
        f"{t['hora']} — {t['nombre']} ({t['telefono']})" for t in del_dia
    ) + "\n\n¿Qué hora cancelar? (HH:MM)")


def _flujo_admin_cancel_hora(numero, body, msg):
    hora  = normalizar_hora(body)
    fecha = get_user_state(numero, "adm_cancel_fecha")

    turnos = obtener_turnos()
    turno  = next((t for t in turnos if t["fecha"] == fecha and t["hora"] == hora), None)

    if not turno:
        msg.body("❌ No se encontró ese turno.")
        set_user_state(numero, "estado", "ADMIN")
        return

    cancelar_turno(turno["telefono"], fecha, hora)
    msg.body(f"✅ Turno cancelado: {fecha} {hora} — {turno['nombre']}")
    set_user_state(numero, "estado", "ADMIN")


def _flujo_bloquear_fecha(numero, body, msg):
    try:
        fecha = datetime.strptime(body.strip(), "%d/%m/%Y").date()
    except ValueError:
        msg.body("❌ Formato inválido. Ingresá dd/mm/yyyy")
        return

    fecha_str = fecha.strftime("%d/%m/%Y")
    set_user_state(numero, "bloqueo_fecha", fecha_str)
    set_user_state(numero, "estado", "BLOQUEAR_HORA")

    horarios = generar_horarios()
    msg.body("Horarios:\n" + "\n".join(horarios) + "\n\n¿Qué hora bloquear? (HH:MM)\nEscribí *todos* para bloquear el día completo.")


def _flujo_bloquear_hora(numero, body, msg):
    fecha = get_user_state(numero, "bloqueo_fecha")

    if body.strip().lower() == "todos":
        for hora in generar_horarios():
            bloquear_horario(fecha, hora)
        msg.body(f"✅ Día {fecha} bloqueado completo.")
    else:
        hora = normalizar_hora(body)
        if hora is None or hora not in generar_horarios():
            msg.body("❌ Hora inválida.")
            return
        bloquear_horario(fecha, hora)
        msg.body(f"✅ Bloqueado: {fecha} {hora}")

    set_user_state(numero, "estado", "ADMIN")
