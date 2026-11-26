# CONFIGURACOES: rede, MQTT, pinos e display.

# Wi-Fi
WIFI_SSID = ""
WIFI_SENHA = ""
WIFI_TIMEOUT = 15  # segundos

# MQTT
MQTT_BROKER = "" # IP do seu computador
MQTT_PORTA = 1883
MQTT_CLIENT_ID = "central_esp32"
MQTT_USUARIO = "central_iot"
MQTT_SENHA = "1234"
TOPICO_CENTRAL = b"iot/central/consulta"
TOPICO_RESPOSTA = b"iot/central/resposta"

# ESP32-C3
PIN_SCL, PIN_SDA = 1, 0
PIN_LINHAS = (9, 8, 7, 10)
PIN_COLUNAS = (20, 5, 6)

# OLED SSD1306
OLED_LARGURA = 128
OLED_ALTURA = 64

