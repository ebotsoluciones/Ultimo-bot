"""
services.py — lógica de negocio del bot de turnos
"""

from datetime import datetime, time
from storage import cargar_json, guardar_json
from config  import TURNOS_FILE, BLOQUEOS_FILE, MENSAJES_FILE

# ═══════════════════════════════════════════════════════════════════════════════
# HORARIOS
# ═══════════════════════════════════════════════════════════════════════════════

HORA_INICIO = time(9, 0)
HORA_FIN    = time(19, 0)
INTERVALO   = 60  # minutos

def generar_horarios() -> list[str]:
    """Devuelve lista de horarios HH:MM entre HORA_INICIO y HORA_FIN."""
    horarios = []
    h, m = HORA_INICIO.hour, HORA_INICIO.minute
    while (h, m) <= (HORA_FIN.hour, HORA_FIN.minute):
        horarios.append(f"{h:02d}:{m:02d}")
        m += INTERVALO
        h += m // 60
        m %= 60
    return horarios

def normalizar_hora(texto: str):
    """Convierte '9', '9:00', '09:00' → '09:00'. Retorna None si inválido."""
    texto = texto.strip().replace(".", ":").replace("-", ":")
    if ":" not in texto:
        texto = texto + ":00"
    partes = texto.split(":")
    try:
        h, m = int(partes[0]), int(partes[1])
        return f"{h:02d}:{m:02d}"
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# TURNOS
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_turnos() -> list[dict]:
    return cargar_json(TURNOS_FILE).get("data", [])

def guardar_turnos(turnos: list[dict]):
    guardar_json(TURNOS_FILE, {"data": turnos})

def agregar_turno(nombre: str, telefono: str, fecha: str, hora: str):
    turnos = obtener_turnos()
    turnos.append({
        "nombre":    nombre,
        "telefono":  telefono,
        "fecha":     fecha,
        "hora":      hora,
        "creado_en": datetime.now().isoformat(),
    })
    guardar_turnos(turnos)

def cancelar_turno(telefono: str, fecha: str, hora: str):
    turnos = obtener_turnos()
    turnos = [
        t for t in turnos
        if not (t["telefono"] == telefono and t["fecha"] == fecha and t["hora"] == hora)
    ]
    guardar_turnos(turnos)

def turnos_usuario(telefono: str) -> list[dict]:
    hoy = datetime.now().date()
    return [
        t for t in obtener_turnos()
        if t["telefono"] == telefono
        and datetime.strptime(t["fecha"], "%d/%m/%Y").date() >= hoy
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# BLOQUEOS
# ═══════════════════════════════════════════════════════════════════════════════

def _obtener_bloqueos() -> list[dict]:
    return cargar_json(BLOQUEOS_FILE).get("data", [])

def _guardar_bloqueos(bloqueos: list[dict]):
    guardar_json(BLOQUEOS_FILE, {"data": bloqueos})

def horario_bloqueado(fecha: str, hora: str) -> bool:
    return any(
        b["fecha"] == fecha and b["hora"] == hora
        for b in _obtener_bloqueos()
    )

def bloquear_horario(fecha: str, hora: str):
    bloqueos = _obtener_bloqueos()
    if not horario_bloqueado(fecha, hora):
        bloqueos.append({"fecha": fecha, "hora": hora})
        _guardar_bloqueos(bloqueos)


# ═══════════════════════════════════════════════════════════════════════════════
# HORARIOS LIBRES
# ═══════════════════════════════════════════════════════════════════════════════

def horarios_libres(fecha: str) -> list[str]:
    turnos   = {t["hora"] for t in obtener_turnos() if t["fecha"] == fecha}
    bloqueos = {b["hora"] for b in _obtener_bloqueos() if b["fecha"] == fecha}
    ocupados = turnos | bloqueos
    return [h for h in generar_horarios() if h not in ocupados]


# ═══════════════════════════════════════════════════════════════════════════════
# MENSAJES
# ═══════════════════════════════════════════════════════════════════════════════

def guardar_mensaje(nombre: str, telefono: str, mensaje: str):
    data = cargar_json(MENSAJES_FILE)
    data.setdefault("data", []).append({
        "nombre":    nombre,
        "telefono":  telefono,
        "mensaje":   mensaje,
        "fecha":     datetime.now().isoformat(),
    })
    guardar_json(MENSAJES_FILE, data)
