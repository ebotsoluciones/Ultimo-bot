import os

# ── Modo test ─────────────────────────────────────────────────────────────────
# En Railway: setear MODO_TEST=false en las variables de entorno
MODO_TEST = os.getenv("MODO_TEST", "true").lower() == "true"

# ── Admins ────────────────────────────────────────────────────────────────────
# En Railway: ADMINS=whatsapp:+5491100000000,whatsapp:+5491199999999
_admins_raw = os.getenv("ADMINS", "")
ADMINS = [a.strip() for a in _admins_raw.split(",") if a.strip()]

# ── Twilio ────────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

# ── Storage ───────────────────────────────────────────────────────────────────
# En Railway el filesystem es efímero.
# STORAGE_BACKEND=memory  →  todo en RAM (se pierde al reiniciar; ideal para pruebas)
# STORAGE_BACKEND=postgres →  persiste en PostgreSQL (recomendado para producción)
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "memory")

# Si usás Postgres, Railway lo inyecta automáticamente como DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Archivos locales (solo se usan si STORAGE_BACKEND=file, entorno local) ────
ESTADO_FILE   = os.getenv("ESTADO_FILE",   "estado.json")
MENSAJES_FILE = os.getenv("MENSAJES_FILE", "mensajes.json")
TURNOS_FILE   = os.getenv("TURNOS_FILE",   "turnos.json")
BLOQUEOS_FILE = os.getenv("BLOQUEOS_FILE", "bloqueos.json")
