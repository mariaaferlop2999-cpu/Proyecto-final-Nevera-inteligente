from machine import Pin, ADC, PWM, SoftI2C
from dht import DHT11
from ssd1306 import SSD1306_I2C
import network
import urequests
import socket
import time

# ==========================================
# IDENTIDAD DEL NODO
# ==========================================

NODE_ID = "nevera01"

# ==========================================
# WIFI
# ==========================================

SSID = "HONOR 90 Lite"
PASSWORD = "andreayepes"

wifi = network.WLAN(network.STA_IF)

wifi.active(True)

wifi.connect(SSID, PASSWORD)

print("Conectando WiFi...")

while not wifi.isconnected():

    time.sleep(1)

print("WiFi conectado")
print(wifi.ifconfig())

# ==========================================
# TELEGRAM
# ==========================================

BOT_TOKEN = "8473116368:AAFFg3ztgA_kG0-pD6OSQOZR3_rnFbKkzfY"
CHAT_ID = "8929308695"

ULTIMO_UPDATE = 0

# ==========================================
# VARIABLES
# ==========================================

temperatura = 0
humedad = 0
luz = 0

estado_puerta = "CERRADA"

estado = "NORMAL"

nivel_riesgo = "BAJO"

ultimo_boton = 1

tiempo_abierta = 0

tiempo_critico = 0

ventilador_manual = False

ultimo_temp = 0
ultimo_hum = 0
ultimo_puerta = 0

eventos = []

# ==========================================
# EVENTOS
# ==========================================

def registrar_evento(texto):

    global eventos

    evento = str(time.time()) + " - " + texto

    print(evento)

    eventos.append(evento)

    if len(eventos) > 10:

        eventos.pop(0)

# ==========================================
# TELEGRAM
# ==========================================

def enviar_telegram(mensaje):

    try:

        mensaje = str(mensaje)

        mensaje = mensaje.replace(" ", "%20")
        mensaje = mensaje.replace("\n", "%0A")

        url = (
            "https://api.telegram.org/bot{}/sendMessage?chat_id={}&text={}"
        ).format(
            BOT_TOKEN,
            CHAT_ID,
            mensaje
        )

        respuesta = urequests.get(url)

        print("Telegram:", respuesta.text)

        respuesta.close()

    except Exception as e:

        print("Error Telegram:", e)

# ==========================================
# COMANDOS TELEGRAM
# ==========================================

# ==========================================
# COMANDOS TELEGRAM
# ==========================================

def leer_telegram():

    global ULTIMO_UPDATE
    global ventilador_manual

    try:

        url = "https://api.telegram.org/bot{}/getUpdates?offset={}".format(
            BOT_TOKEN,
            ULTIMO_UPDATE + 1
        )

        r = urequests.get(url)

        datos = r.json()

        r.close()

        if "result" not in datos:
            return

        for mensaje in datos["result"]:

            ULTIMO_UPDATE = mensaje["update_id"]

            # VALIDAR MENSAJES
            if "message" not in mensaje:
                continue

            if "text" not in mensaje["message"]:
                continue

            texto = mensaje["message"]["text"].strip()

            print("Comando recibido:", texto)

 # ==================================
# COMANDOS
# ==================================

            if texto == "/estado":

                enviar_telegram(
                    "TEMP: " + str(round(temperatura,1)) +
                    "\nHUM: " + str(round(humedad,1)) +
                    "\nLUZ: " + str(luz) +
                    "\nESTADO: " + estado
                )

            elif texto == "/temp":

                enviar_telegram(
                    "TEMPERATURA: " +
                    str(round(temperatura,1)) + " C"
                )

            elif texto == "/humedad":

                enviar_telegram(
                    "HUMEDAD: " +
                    str(round(humedad,1)) + " %"
                )

            elif texto == "/luz":

                enviar_telegram(
                    "LUZ: " + str(luz)
                )

            elif texto == "/general":

                enviar_telegram(
                    "ESTADO: " + estado
                )

    except Exception as e:

        print("Error Telegram comandos:", e)
# ==========================================
# PAGINA WEB
# ==========================================

def pagina_web():

    return f"""

    <html>

    <head>

    <meta http-equiv="refresh" content="2">

    <style>

    body {{

        background:pink;
        color:black
        text-align:center;
        font-family:Arial;

    }}

    .card {{

        background:white;
        padding:15px;
        margin:10px;
        border-radius:15px;
        display:inline-block;
        width:220px;

    }}

    </style>

    </head>

    <body>

    <h1>NEVERA</h1>

    <div class="card">
    <h2>Temperatura</h2>
    <h1>{temperatura} C</h1>
    </div>

    <div class="card">
    <h2>Humedad</h2>
    <h1>{humedad} %</h1>
    </div>

    <div class="card">
    <h2>Luz</h2>
    <h1>{luz}</h1>
    </div>

    <div class="card">
    <h2>Puerta</h2>
    <h1>{estado_puerta}</h1>
    </div>

    <div class="card">
    <h2>Estado</h2>
    <h1>{estado}</h1>
    </div>

    <div class="card">
    <h2>Riesgo</h2>
    <h1>{nivel_riesgo}</h1>
    </div>

    <div class="card">
    <h2>Ventilador</h2>
    <h1>{"ON" if ventilador.value() else "OFF"}</h1>
    </div>

    </body>

    </html>

    """

# ==========================================
# SERVIDOR WEB
# ==========================================

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(("", 80))

server.listen(1)

server.settimeout(0.2)

print("WEB OK")

print("IP:", wifi.ifconfig()[0])

# ==========================================
# PINES
# ==========================================

dht = DHT11(Pin(15))

ldr = ADC(Pin(34))
ldr.atten(ADC.ATTN_11DB)

reed = Pin(4, Pin.IN, Pin.PULL_UP)

# LEDS

led_rojo = Pin(25, Pin.OUT)

led_verde = Pin(23, Pin.OUT)

led_azul = Pin(27, Pin.OUT)

# BUZZER

buzzer = PWM(Pin(26))
buzzer.duty(0)

# SERVO

servo = PWM(Pin(13), freq=50)

# VENTILADOR

ventilador = Pin(33, Pin.OUT)
ventilador.off()

# BOTON PULL UP

boton = Pin(14, Pin.IN, Pin.PULL_UP)

# OLED

i2c = SoftI2C(scl=Pin(22), sda=Pin(21))

oled = SSD1306_I2C(128, 64, i2c)

# ==========================================
# LEDS
# ==========================================

def apagar_leds():

    led_rojo.off()
    led_verde.off()
    led_azul.off()

def led_normal():

    apagar_leds()

    led_verde.on()

def led_alerta():

    apagar_leds()

    led_azul.on()

def led_critico():

    apagar_leds()

    led_rojo.on()

# ==========================================
# BUZZER
# ==========================================

def apagar_buzzer():

    buzzer.duty(0)

def buzzer_alerta():

    buzzer.freq(1200)
    buzzer.duty(25)

def buzzer_critico():

    buzzer.freq(2000)
    buzzer.duty(50)

# ==========================================
# SERVO
# ==========================================

angulo_actual = 90

def mover_servo_lento(destino):

    global angulo_actual

    paso = 1 if destino > angulo_actual else -1

    for angulo in range(
        angulo_actual,
        destino,
        paso
    ):

        duty = int(
            26 + (128 - 26) * angulo / 180
        )

        servo.duty(duty)

        time.sleep_ms(8)

    angulo_actual = destino

# ==========================================
# INICIO
# ==========================================

print("NEVERA INICIADO")

mover_servo_lento(90)

led_normal()

enviar_telegram("MEDISAFE INICIADO")

# ==========================================
# LOOP
# ==========================================

while True:

    try:

        # ==================================
        # WEB
        # ==================================

        try:

            conn, addr = server.accept()

            request = conn.recv(1024)

            html = pagina_web()

            conn.send("HTTP/1.1 200 OK\r\n")
            conn.send("Content-Type: text/html\r\n\r\n")

            conn.sendall(html)

            conn.close()

        except:

            pass

        # ==================================
        # SENSORES
        # ==================================

        dht.measure()

        temperatura = dht.temperature()

        humedad = dht.humidity()

        luz = ldr.read()

        reed_estado = reed.value()

        # ==================================
        # PUERTA
        # ==================================

        if reed_estado == 0:

            estado_puerta = "CERRADA"

            puerta_abierta = False

            tiempo_abierta = 0

        else:

            estado_puerta = "ABIERTA"

            puerta_abierta = True

            tiempo_abierta += 1

        # ==================================
        # BOTON
        # ==================================

        estado_boton = boton.value()

        if estado_boton == 0 and ultimo_boton == 1:

            print("BOTON PRESIONADO")

            registrar_evento("BOTON PRESIONADO")

            enviar_telegram("BOTON MANUAL")

            mover_servo_lento(0)

            time.sleep(5)

            mover_servo_lento(90)

        ultimo_boton = estado_boton

        # ==================================
        # LOGICA DIFUSA
        # ==================================

        riesgo = 0

        if temperatura >= 29:

            riesgo += 20

        if temperatura >= 32:

            riesgo += 40

        if humedad >= 62:

            riesgo += 20

        if humedad >= 65:

            riesgo += 40

        if puerta_abierta:

            riesgo += 30

        # ==================================
        # NIVEL RIESGO
        # ==================================

        if riesgo < 30:

            nivel_riesgo = "BAJO"

        elif riesgo < 70:

            nivel_riesgo = "MEDIO"

        else:

            nivel_riesgo = "ALTO"

        # ==================================
        # VENTILADOR
        # ==================================

        if estado_puerta == "CERRADA":

            if temperatura >= 28 or humedad >= 62:

                ventilador.on()

            else:

                if not ventilador_manual:

                    ventilador.off()

        else:

            ventilador.off()

        # ==================================
        # ESTADOS
        # ==================================

        if nivel_riesgo == "BAJO":

            estado = "NORMAL"

            tiempo_critico = 0

            led_normal()

            apagar_buzzer()

        elif nivel_riesgo == "MEDIO":

            estado = "ALERTA"

            tiempo_critico = 0

            led_alerta()

            buzzer_alerta()

        else:

            estado = "CRITICO"

            led_critico()

            buzzer_critico()

            tiempo_critico += 1

            if tiempo_critico >= 15:

                print("CERRANDO PUERTA")

                enviar_telegram(
                    "CERRANDO PUERTA AUTOMATICAMENTE"
                )

                registrar_evento(
                    "CIERRE AUTOMATICO"
                )

                mover_servo_lento(90)

                tiempo_critico = 0

        # ==================================
        # ALERTAS TELEGRAM
        # ==================================

        ahora = time.time()

        if temperatura >= 30:

            if ahora - ultimo_temp > 20:

                enviar_telegram(
                    "TEMP ALTA: " +
                    str(temperatura)
                )

                ultimo_temp = ahora

        if humedad >= 75:

            if ahora - ultimo_hum > 20:

                enviar_telegram(
                    "HUMEDAD ALTA: " +
                    str(humedad)
                )

                ultimo_hum = ahora

        if puerta_abierta:

            if ahora - ultimo_puerta > 20:

                enviar_telegram(
                    "PUERTA ABIERTA"
                )

                ultimo_puerta = ahora

        # ==================================
        # TELEGRAM
        # ==================================

        leer_telegram()

        # ==================================
        # OLED
        # ==================================

        oled.fill(0)

        oled.text("NEVERA", 10, 0)

        oled.text(
            "T:" + str(temperatura),
            0,
            15
        )

        oled.text(
            "H:" + str(humedad),
            0,
            28
        )

        oled.text(
            "L:" + str(luz),
            0,
            41
        )

        oled.text(
            nivel_riesgo,
            0,
            54
        )

        oled.show()

        # ==================================
        # SERIAL
        # ==================================

        print("================")

        print("Temp:", temperatura)

        print("Hum:", humedad)

        print("Luz:", luz)

        print("Puerta:", estado_puerta)

        print("Riesgo:", nivel_riesgo)

        print("Ventilador:", ventilador.value())

    except Exception as e:

        print("ERROR:", e)

    time.sleep(1)