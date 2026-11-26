import json
import logging
import re
import threading

import paho.mqtt.client as mqtt

from . import database
from .config import (
    MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID,
    MQTT_KEEPALIVE, TOPIC_CENTRAL, TOPIC_CENTRAL_RESPONSE, TOPIC_BOX_RELEASE,
)

log = logging.getLogger("iot.mqtt")
ESTADOS_CENTRAL = {"EM_PREPARO", "PRONTO"}


def normalizar_caixa(valor):
    numero = str(valor or "").strip()
    if re.fullmatch(r"[0-9]", numero):
        numero = numero.zfill(2)
    if not re.fullmatch(r"[0-9]{2}", numero):
        return None
    n = int(numero)
    if not 1 <= n <= 99:
        return None
    return numero


class MQTTService:
    def __init__(self):
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=MQTT_CLIENT_ID,
            protocol=mqtt.MQTTv311,
        )
        if MQTT_USERNAME:
            self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self._connected = threading.Event()

    @property
    def conectado(self):
        return self._connected.is_set()

    def start(self):
        self.client.connect(MQTT_HOST, MQTT_PORT, MQTT_KEEPALIVE)
        self.client.loop_start()

    def stop(self):
        try:
            self.client.disconnect()
        finally:
            self.client.loop_stop()

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code.is_failure:
            log.error("Falha ao conectar ao broker MQTT: %s", reason_code)
            return
        client.subscribe([(TOPIC_CENTRAL, 1), (TOPIC_BOX_RELEASE, 1)])
        self._connected.set()
        log.info("Conectado ao MQTT %s:%s", MQTT_HOST, MQTT_PORT)

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self._connected.clear()
        log.warning("Desconectado do broker MQTT: %s", reason_code)

    def publicar(self, topico, dados):
        if not self.conectado:
            log.warning("Mensagem não publicada: MQTT desconectado")
            return False
        resultado = self.client.publish(topico, json.dumps(dados, ensure_ascii=False), qos=1)
        return resultado.rc == mqtt.MQTT_ERR_SUCCESS

    def _on_message(self, client, userdata, mensagem):
        try:
            dados = json.loads(mensagem.payload.decode("utf-8"))
            if not isinstance(dados, dict):
                raise ValueError("Payload precisa ser um objeto JSON")
        except Exception as erro:
            log.warning("JSON MQTT inválido em %s: %s", mensagem.topic, erro)
            if mensagem.topic == TOPIC_CENTRAL:
                self.publicar(TOPIC_CENTRAL_RESPONSE, {
                    "aceito": False, "mensagem": "RESPOSTA INVALIDA",
                    "motivo": "Payload não é um objeto JSON válido"
                })
            return

        if mensagem.topic == TOPIC_CENTRAL:
            self._tratar_central(dados)
        elif mensagem.topic.startswith("iot/caixas/") and mensagem.topic.endswith("/solicitacao"):
            self._tratar_liberacao(mensagem.topic, dados)

    def _tratar_central(self, dados):
        caixa = normalizar_caixa(dados.get("caixa", dados.get("numero_caixa")))
        estado = str(dados.get("estado", dados.get("status", ""))).strip().upper()
        if caixa is None:
            self.publicar(TOPIC_CENTRAL_RESPONSE, {
                "aceito": False, "mensagem": "CAIXA NÃO CADASTRADA",
                "motivo": "Número da caixa inválido. Use 01 a 99.",
                "recebido": dados,
            })
            return
        if estado not in ESTADOS_CENTRAL:
            self.publicar(TOPIC_CENTRAL_RESPONSE, {
                "aceito": False, "caixa": caixa, "mensagem": "CAIXA NÃO CADASTRADA",
                "motivo": "Estado inválido", "estados_permitidos": sorted(ESTADOS_CENTRAL),
            })
            return
        if not database.caixa_ativa(caixa):
            self.publicar(TOPIC_CENTRAL_RESPONSE, {
                "aceito": False, "caixa": caixa,
                "motivo": "Caixa não cadastrada ou desativada",
                "mensagem": "CAIXA NÃO CADASTRADA",
            })
            return

        database.atualizar_estado(caixa, estado)
        self.publicar(TOPIC_CENTRAL_RESPONSE, {
            "aceito": True, "caixa": caixa, "estado": estado,
            "mensagem": "SOLICITACAO ACEITA",
        })
        self.publicar(f"iot/caixas/{caixa}/comando", {"caixa": caixa, "estado": estado})
        log.info("Caixa %s atualizada para %s", caixa, estado)

    def _tratar_liberacao(self, topico, dados):
        partes = topico.split("/")
        caixa_topico = partes[2] if len(partes) == 4 else ""
        caixa = normalizar_caixa(dados.get("caixa", caixa_topico))
        estado_solicitado = str(dados.get("estado", "")).strip().upper()

        if caixa is None or caixa != caixa_topico:
            self._responder_caixa(caixa_topico if caixa_topico else "00", False,
                "Número da caixa inválido ou diferente do tópico")
            return
        if estado_solicitado != "NAO_USADA":
            self._responder_caixa(caixa, False, "Solicitação deve pedir o estado NAO_USADA")
            return

        aceito, mensagem, estado_atual = database.liberar_se_pronta(caixa)
        if aceito:
            self.publicar(f"iot/caixas/{caixa}/resposta", {
                "aceito": True, "caixa": caixa, "estado": "NAO_USADA",
                "mensagem": "CAIXA LIBERADA",
            })
            log.info("Caixa %s liberada", caixa)
        else:
            self.publicar(f"iot/caixas/{caixa}/resposta", {
                "aceito": False, "caixa": caixa, "motivo": mensagem,
                "estado_atual": estado_atual, "mensagem": "LIBERACAO REJEITADA",
            })

    def _responder_caixa(self, numero, aceito, motivo):
        self.publicar(f"iot/caixas/{numero}/resposta", {
            "aceito": aceito, "caixa": numero, "motivo": motivo,
            "mensagem": "LIBERACAO REJEITADA",
        })
