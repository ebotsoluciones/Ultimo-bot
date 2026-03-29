"""
app.py — servidor Flask para el bot de turnos en WhatsApp (Twilio)
Deploy: Railway
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from handlers import procesar

app = Flask(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Health check — Railway lo usa para saber que el servicio está vivo
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# ─────────────────────────────────────────────────────────────────────────────
# Webhook de Twilio WhatsApp
# Twilio envía POST a /webhook con los campos:
#   From  →  whatsapp:+549XXXXXXXXXX
#   Body  →  texto del mensaje
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/webhook", methods=["POST"])
def webhook():
    numero = request.form.get("From", "")
    body   = request.form.get("Body", "").strip()

    resp = MessagingResponse()
    procesar(numero, body, resp)

    return str(resp), 200, {"Content-Type": "text/xml"}

# ─────────────────────────────────────────────────────────────────────────────
# Entrada
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Railway inyecta PORT automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
