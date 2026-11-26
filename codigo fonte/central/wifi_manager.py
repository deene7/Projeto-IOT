# CONEXÃO E MONITORAMENTO DO WI-FI.

import network
import time
import config as c


class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)

    def conectado(self):
        return self.wlan.active() and self.wlan.isconnected()

    def endereco_ip(self):
        return self.wlan.ifconfig()[0] if self.conectado() else None

    def conectar(self):
        self.wlan.active(True)

        if self.wlan.isconnected():
            return True

        print("Conectando ao Wi-Fi:", c.WIFI_SSID)
        self.wlan.connect(c.WIFI_SSID, c.WIFI_SENHA)
        inicio = time.ticks_ms()

        while not self.wlan.isconnected():
            passou = time.ticks_diff(time.ticks_ms(), inicio)

            if passou >= c.WIFI_TIMEOUT * 1000:
                print("Tempo esgotado ao conectar ao Wi-Fi.")
                return False

            time.sleep_ms(250)

        print("Wi-Fi conectado. IP:", self.wlan.ifconfig()[0])
        return True

