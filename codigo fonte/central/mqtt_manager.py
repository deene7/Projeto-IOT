# COMUNICAÇÃO MQTT COM O SERVIDOR FASTAPI.

import time
import ujson
from umqtt.simple import MQTTClient
import config as c

class MQTTManager:
    TEMPO_RESPOSTA_MS = 8000

    def __init__(self):
        self.cliente = None
        self.resposta = None
        self.pendente = False
        self.inicio_espera = 0

    def conectado(self):
        return self.cliente is not None

    def solicitacao_pendente(self):
        return self.pendente

    def _ao_receber(self, topico, mensagem):
        try:
            texto = mensagem.decode() if isinstance(mensagem, bytes) else mensagem
            resposta = ujson.loads(texto)

            if not isinstance(resposta, dict):
                raise ValueError("Resposta MQTT inválida")

            self.resposta = resposta
            print("Resposta MQTT:", resposta)

        except Exception as erro:
            print("Erro ao interpretar resposta:", repr(erro))
            self.resposta = {
                "aceito": False,
                "mensagem": "RESPOSTA INVALIDA",
                "motivo": "Resposta do servidor invalida"
            }

    def conectar(self):
        if self.cliente is not None:
            return True

        novo_cliente = None

        try:
            novo_cliente = MQTTClient(
                c.MQTT_CLIENT_ID.encode(),
                c.MQTT_BROKER,
                c.MQTT_PORTA,
                c.MQTT_USUARIO.encode(),
                c.MQTT_SENHA.encode(),
                keepalive=60
            )

            novo_cliente.set_callback(self._ao_receber)
            novo_cliente.connect()
            novo_cliente.subscribe(c.TOPICO_RESPOSTA)

            self.cliente = novo_cliente
            print("MQTT conectado. Tópico:", c.TOPICO_RESPOSTA)
            return True

        except Exception as erro:
            print("Falha ao conectar MQTT:", repr(erro))

            if novo_cliente is not None:
                try:
                    novo_cliente.disconnect()
                except Exception:
                    pass

            self.cliente = None
            return False

    def publicar(self, caixa, estado):
        if self.cliente is None:
            print("MQTT não conectado.")
            return False

        if self.pendente:
            print("Já existe uma solicitação pendente.")
            return False

        mensagem = {"caixa": str(caixa), "estado": str(estado)}

        try:
            self.resposta = None
            self.cliente.publish(c.TOPICO_CENTRAL, ujson.dumps(mensagem).encode())
            self.inicio_espera = time.ticks_ms()
            self.pendente = True
            print("Solicitação enviada:", mensagem)
            return True

        except Exception as erro:
            print("Erro ao publicar MQTT:", repr(erro))
            self._desconectar_cliente()
            return False

    def verificar_resposta(self):
        if self.cliente is None:
            return None

        try:
            self.cliente.check_msg()

        except Exception as erro:
            print("Erro na comunicação MQTT:", repr(erro))
            self._desconectar_cliente()

            if self.pendente:
                self.pendente = False
                return {
                    "aceito": False,
                    "mensagem": "FALHA MQTT",
                    "motivo": "Conexao interrompida"
                }

            return None

        if self.resposta is not None:
            resposta = self.resposta
            self.resposta = None
            self.pendente = False
            return resposta

        passou = time.ticks_diff(time.ticks_ms(), self.inicio_espera)

        if self.pendente and passou >= self.TEMPO_RESPOSTA_MS:
            self.pendente = False
            return {
                "aceito": False,
                "mensagem": "SEM RESPOSTA",
                "motivo": "Tempo limite de resposta excedido"
            }

        return None

    def _desconectar_cliente(self):
        if self.cliente is not None:
            try:
                self.cliente.disconnect()
            except Exception:
                pass

        self.cliente = None

    def desconectar(self):
        self.pendente = False
        self.resposta = None
        self._desconectar_cliente()
        print("MQTT desconectado.")

