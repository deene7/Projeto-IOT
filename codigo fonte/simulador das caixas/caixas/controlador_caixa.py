class ControladorCaixa:

    ESTADOS_VALIDOS = (
        "NAO_USADA",
        "EM_PREPARO",
        "PRONTO"
    )

    def __init__(self, numero):
        self.numero = numero
        self.estado = "NAO_USADA"
        self.aguardando_resposta = False

    def atualizar_estado(self, novo_estado):
        if novo_estado not in self.ESTADOS_VALIDOS:
            return False

        self.estado = novo_estado
        self.aguardando_resposta = False

        return True

    def solicitar_liberacao(self):
        if self.estado != "PRONTO":
            return False

        if self.aguardando_resposta:
            return False

        self.aguardando_resposta = True
        return True

    def cancelar_solicitacao(self):
        self.aguardando_resposta = False