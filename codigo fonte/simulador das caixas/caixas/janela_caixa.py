import tkinter as tk
from tkinter import ttk

from caixas.controlador_caixa import ControladorCaixa


class JanelaCaixa:

    def __init__(self, root, numero, mqtt, ao_fechar=None):

        self.numero = numero
        self.mqtt = mqtt
        self.ao_fechar = ao_fechar

        self.controlador = ControladorCaixa(numero)

        self.janela = tk.Toplevel(root)
        self.janela.title(f"Caixa {numero}")
        self.janela.geometry("280x290")
        self.janela.resizable(False, False)

        self.led_ligado = False
        self.after_led = None

        self.criar_interface()

        self.janela.protocol(
            "WM_DELETE_WINDOW",
            self.fechar
        )

        self.atualizar_interface()

    def criar_interface(self):

        ttk.Label(
            self.janela,
            text=f"CAIXA {self.numero}",
            font=("Arial", 16, "bold")
        ).pack(pady=15)

        self.led = tk.Canvas(
            self.janela,
            width=80,
            height=80,
            highlightthickness=0
        )
        self.led.pack()

        self.luz = self.led.create_oval(
            15, 15, 65, 65,
            fill="gray",
            outline="black",
            width=2
        )

        self.texto_estado = ttk.Label(
            self.janela,
            text="NÃO UTILIZADA",
            font=("Arial", 11, "bold")
        )
        self.texto_estado.pack(pady=10)

        self.texto_status = ttk.Label(
            self.janela,
            text="Aguardando comandos..."
        )
        self.texto_status.pack()

        self.botao = ttk.Button(
            self.janela,
            text="LIBERAR CAIXA",
            command=self.solicitar_liberacao,
            state="disabled"
        )
        self.botao.pack(pady=12)

    def receber_comando(self, dados):

        estado = dados.get("estado")

        if self.controlador.atualizar_estado(estado):
            self.texto_status.config(
                text="Comando recebido do servidor"
            )

            self.atualizar_interface()

    def receber_resposta(self, dados):

        aceito = dados.get("aceito", False)

        if aceito:
            self.controlador.atualizar_estado("NAO_USADA")

            self.texto_status.config(
                text="Caixa liberada com sucesso"
            )

        else:
            self.controlador.cancelar_solicitacao()

            motivo = dados.get(
                "motivo",
                "Solicitação recusada"
            )

            self.texto_status.config(
                text=str(motivo)
            )

        self.atualizar_interface()

    def atualizar_interface(self):

        estado = self.controlador.estado

        nomes = {
            "NAO_USADA": "NÃO UTILIZADA",
            "EM_PREPARO": "EM PREPARO",
            "PRONTO": "PEDIDO PRONTO"
        }

        self.texto_estado.config(text=nomes[estado])

        pode_liberar = (
            estado == "PRONTO"
            and not self.controlador.aguardando_resposta
        )

        self.botao.config(
            state="normal" if pode_liberar else "disabled"
        )

        if estado == "PRONTO":
            if self.after_led is None:
                self.piscar_led()
        else:
            self.parar_led()

    def piscar_led(self):

        if not self.janela.winfo_exists():
            return

        if self.controlador.estado != "PRONTO":
            self.parar_led()
            return

        self.led_ligado = not self.led_ligado

        cor = "orange" if self.led_ligado else "gray"

        self.led.itemconfig(
            self.luz,
            fill=cor
        )

        self.after_led = self.janela.after(
            500,
            self.piscar_led
        )

    def parar_led(self):

        if self.after_led is not None:
            self.janela.after_cancel(self.after_led)
            self.after_led = None

        self.led_ligado = False

        self.led.itemconfig(
            self.luz,
            fill="gray"
        )

    def solicitar_liberacao(self):

        if not self.controlador.solicitar_liberacao():
            return

        self.botao.config(state="disabled")

        self.texto_status.config(
            text="Enviando solicitação..."
        )

        sucesso = self.mqtt.solicitar_liberacao(
            self.numero
        )

        if not sucesso:
            self.controlador.cancelar_solicitacao()

            self.texto_status.config(
                text="Falha ao enviar. Verifique MQTT."
            )

            self.atualizar_interface()

    def fechar(self):

        self.parar_led()

        if self.ao_fechar:
            self.ao_fechar()

        self.janela.destroy()