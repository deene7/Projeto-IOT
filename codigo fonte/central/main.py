# PROGRAMA PRINCIPAL DA CENTRAL ESP32-C3.

import time
from display import Display
from keyboard import Teclado
from wifi_manager import WiFiManager
from mqtt_manager import MQTTManager


class Central:
    INTERVALO_RECONEXAO_MS = 5000
    TEMPO_MINIMO_AGUARDANDO_MS = 1000

    def __init__(self):
        self.display = Display()
        self.teclado = Teclado()
        self.wifi = WiFiManager()
        self.mqtt = MQTTManager()

        self.entrada = ""
        self.ultimo_teste_conexao = 0
        self.inicio_aguardando = 0

    def mostrar_inicio(self):
        self.entrada = ""
        self.display.tela_inicial()

    @staticmethod
    def normalizar_numero(numero):
        return "0" + numero if len(numero) == 1 else numero

    @staticmethod
    def numero_valido(numero):
        valor = int(numero) if numero.isdigit() else 0
        return 1 <= valor <= 99

    def garantir_conexoes(self):
        agora = time.ticks_ms()

        if time.ticks_diff(agora, self.ultimo_teste_conexao) < self.INTERVALO_RECONEXAO_MS:
            return

        self.ultimo_teste_conexao = agora

        if not self.wifi.conectado():
            print("Reconectando Wi-Fi...")

            if not self.wifi.conectar():
                self.display.mostrar("SEM WIFI", 32)
                return

        if not self.mqtt.conectado():
            print("Reconectando MQTT...")

            if not self.mqtt.conectar():
                self.display.mostrar("SEM MQTT", 32)
                return

        if not self.mqtt.solicitacao_pendente() and self.entrada == "":
            self.display.tela_inicial()

    def enviar_solicitacao(self, estado):
        if self.entrada == "":
            self.display.mostrar("DIGITE A CAIXA", 8)
            time.sleep_ms(1200)
            self.mostrar_inicio()
            return

        numero = self.normalizar_numero(self.entrada)

        if not self.numero_valido(numero):
            self.display.caixa_recusada()
            time.sleep_ms(1200)
            self.mostrar_inicio()
            return

        if not self.wifi.conectado():
            self.display.mostrar("SEM WIFI", 32)
            time.sleep_ms(1200)
            self.mostrar_inicio()
            return

        if not self.mqtt.conectado():
            self.display.mostrar("SEM MQTT", 32)
            time.sleep_ms(1200)
            self.mostrar_inicio()
            return

        if self.mqtt.publicar(numero, estado):
            self.inicio_aguardando = time.ticks_ms()
            self.display.mostrar_aguardando()
        else:
            self.display.mostrar_erro()
            time.sleep_ms(1200)
            self.mostrar_inicio()

    def tratar_resposta(self, resposta):
        passou = time.ticks_diff(time.ticks_ms(), self.inicio_aguardando)
        restante = self.TEMPO_MINIMO_AGUARDANDO_MS - passou

        if restante > 0:
            time.sleep_ms(restante)

        aceito = resposta.get("aceito") is True
        caixa = resposta.get("caixa", "")
        estado = resposta.get("estado", "")
        mensagem = resposta.get("mensagem", "")

        print("Resultado:", resposta)

        if aceito:
            if estado:
                self.display.mostrar_estado(caixa, estado)
            else:
                self.display.mostrar("SOLICITACAO OK", 8)
        elif mensagem in ("SEM RESPOSTA", "FALHA MQTT"):
            self.display.mostrar_erro()
        else:
            self.display.caixa_recusada()
            print("Motivo:", resposta.get("motivo", ""))

        time.sleep_ms(1800)
        self.mostrar_inicio()

    def tratar_tecla(self, tecla):
        if tecla is None:
            return

        print("Tecla:", tecla)

        if tecla == "*":
            self.enviar_solicitacao("EM_PREPARO")

        elif tecla == "#":
            self.enviar_solicitacao("PRONTO")

        elif tecla.isdigit():
            if len(self.entrada) == 2:
                self.entrada = ""
            self.entrada += tecla
            self.display.mostrar_caixa(self.entrada)

    def iniciar(self):
        self.display.tela_inicial()
        print("Iniciando central IoT...")

        if not self.wifi.conectar():
            self.display.mostrar("SEM WIFI", 32)
            print("Wi-Fi indisponível.")
            return False

        if not self.mqtt.conectar():
            self.display.mostrar("SEM MQTT", 32)
            print("MQTT indisponível.")
            return False

        self.display.tela_inicial()
        print("Central pronta.")
        return True

    def executar(self):
        self.iniciar()

        while True:
            self.garantir_conexoes()

            if self.mqtt.solicitacao_pendente():
                resposta = self.mqtt.verificar_resposta()

                if resposta is not None:
                    self.tratar_resposta(resposta)

                time.sleep_ms(50)
                continue

            if self.mqtt.conectado():
                self.mqtt.verificar_resposta()

            self.tratar_tecla(self.teclado.ler_tecla())
            time.sleep_ms(30)


if __name__ == "__main__":
    Central().executar()

