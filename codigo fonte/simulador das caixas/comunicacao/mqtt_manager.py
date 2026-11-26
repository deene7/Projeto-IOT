import json

import paho.mqtt.client as mqtt

import config


class MQTTManager:

    def __init__(self, fila_eventos):
        self.fila_eventos = fila_eventos
        self.cliente = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311
        )

        if config.MQTT_USUARIO:
            self.cliente.username_pw_set(
                config.MQTT_USUARIO,
                config.MQTT_SENHA
            )

        self.cliente.on_connect = self.ao_conectar
        self.cliente.on_disconnect = self.ao_desconectar
        self.cliente.on_message = self.ao_receber

    def conectar(self):
        try:
            self.cliente.connect_async(
                config.MQTT_BROKER,
                config.MQTT_PORTA,
                config.MQTT_KEEPALIVE
            )

            self.cliente.loop_start()

        except Exception as erro:
            self.fila_eventos.put({
                "tipo": "conexao",
                "conectado": False,
                "mensagem": str(erro)
            })

    def ao_conectar(
        self, cliente, userdata, flags, reason_code, properties
    ):
        if reason_code.is_failure:
            self.fila_eventos.put({
                "tipo": "conexao",
                "conectado": False,
                "mensagem": str(reason_code)
            })
            return

        cliente.subscribe(config.TOPICO_COMANDO)
        cliente.subscribe(config.TOPICO_RESPOSTA)
        cliente.subscribe(config.TOPICO_RESPOSTA_CENTRAL)

        self.fila_eventos.put({
            "tipo": "conexao",
            "conectado": True,
            "mensagem": "Conectado ao Mosquitto"
        })

    def ao_desconectar(
        self, cliente, userdata, disconnect_flags,
        reason_code, properties
    ):
        self.fila_eventos.put({
            "tipo": "conexao",
            "conectado": False,
            "mensagem": "Desconectado do Mosquitto"
        })

    def ao_receber(self, cliente, userdata, mensagem):
        try:
            dados = json.loads(mensagem.payload.decode("utf-8"))
            if not isinstance(dados, dict):
                return

            if mensagem.topic == config.TOPICO_RESPOSTA_CENTRAL:
                self.fila_eventos.put({"tipo": "resposta_central", "dados": dados})
                return

            partes = mensagem.topic.split("/")

            # Formato esperado:
            # iot/caixas/01/comando
            # iot/caixas/01/resposta

            if len(partes) != 4:
                return

            if partes[0] != "iot" or partes[1] != "caixas":
                return

            numero = partes[2]
            tipo = partes[3]

            self.fila_eventos.put({
                "tipo": "mensagem",
                "caixa": numero,
                "subtipo": tipo,
                "dados": dados
            })

        except Exception as erro:
            self.fila_eventos.put({
                "tipo": "erro",
                "mensagem": str(erro)
            })

    def solicitar_liberacao(self, numero):
        return self.publicar_estado(config.TOPICO_SOLICITACAO.format(numero), numero, "NAO_USADA")

    def enviar_comando_central(self, numero, estado):
        return self.publicar_estado(config.TOPICO_CENTRAL, numero, estado)

    def publicar_estado(self, topico, numero, estado):
        if not self.cliente.is_connected():
            return False

        mensagem = {
            "caixa": numero,
            "estado": estado
        }

        try:
            resultado = self.cliente.publish(
                topico,
                json.dumps(mensagem),
                qos=1
            )

            return resultado.rc == mqtt.MQTT_ERR_SUCCESS

        except Exception:
            return False

    def desconectar(self):
        self.cliente.disconnect()
        self.cliente.loop_stop()
