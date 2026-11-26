import tkinter as tk
from tkinter import ttk, messagebox
from queue import Queue, Empty

from caixas.janela_caixa import JanelaCaixa
from comunicacao.mqtt_manager import MQTTManager


class Simulador:

    def __init__(self, root):

        self.root = root
        self.root.title("Simulador de Caixas IoT")
        self.root.resizable(False, False)

        self.janelas = {}
        self.comando_pendente = None
        self.timeout_central = None

        # Fila para comunicação entre MQTT e Tkinter
        self.fila_eventos = Queue()

        # Gerenciador MQTT único
        self.mqtt = MQTTManager(self.fila_eventos)
        self.mqtt.conectar()

        self.criar_interface()

        for numero in ("01", "02", "03"):
            self.abrir_caixa(numero)

        self.processar_eventos()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.fechar
        )

    def criar_interface(self):

        ttk.Label(
            self.root,
            text="SIMULADOR DE CAIXAS IoT",
            font=("Arial", 16, "bold")
        ).pack(pady=20)

        ttk.Label(
            self.root,
            text="Gerenciamento das caixas virtuais"
        ).pack()

        ttk.Label(
            self.root,
            text="Número da caixa (01 a 99):"
        ).pack(pady=(20, 5))

        self.entrada = ttk.Entry(
            self.root,
            justify="center",
            width=15
        )
        self.entrada.pack()

        ttk.Button(
            self.root,
            text="Abrir caixa",
            command=self.adicionar_caixa
        ).pack(pady=12)

        self.status = ttk.Label(
            self.root,
            text="Conectando ao MQTT..."
        )
        self.status.pack(pady=10)

        painel = ttk.LabelFrame(self.root, text="Central virtual", padding=12)
        painel.pack(padx=20, pady=(0, 15), fill="x")
        self.botoes_central = [
            ttk.Button(painel, text="Registrar preparo (*)",
                       command=lambda: self.enviar_comando("EM_PREPARO")),
            ttk.Button(painel, text="Marcar pronto (#)",
                       command=lambda: self.enviar_comando("PRONTO")),
        ]
        for botao in self.botoes_central:
            botao.pack(side="top", fill="x", pady=2)
        self.status_central = ttk.Label(painel, text="Digite o número da caixa acima.", wraplength=320)
        self.status_central.pack(pady=(8, 0))

    def validar_numero(self, numero):

        if not (1 <= len(numero) <= 2 and numero.isascii() and numero.isdecimal()):
            return False

        numero = int(numero)

        return 1 <= numero <= 99

    def adicionar_caixa(self):
        numero = self.entrada.get().strip()
        if not self.validar_numero(numero):
            messagebox.showerror(
                "Número inválido",
                "Use números de 01 a 99."
            )
            return

        self.abrir_caixa(numero.zfill(2))

    def enviar_comando(self, estado):
        numero = self.entrada.get().strip()
        if not self.validar_numero(numero):
            self.status_central.config(text="Use 01 a 99.")
            return

        numero = numero.zfill(2)
        if not self.mqtt.enviar_comando_central(numero, estado):
            self.status_central.config(text="Falha no envio. Verifique a conexão MQTT.")
            return

        self.comando_pendente = (numero, estado)
        for botao in self.botoes_central:
            botao.state(["disabled"])
        self.status_central.config(text=f"Caixa {numero} · Aguardando o backend…")
        self.timeout_central = self.root.after(8000, self.sem_resposta_central)

    def sem_resposta_central(self):
        self.timeout_central = None
        self.finalizar_comando("Sem resposta do backend. Confira o FastAPI.")

    def finalizar_comando(self, mensagem):
        if self.timeout_central is not None:
            self.root.after_cancel(self.timeout_central)
            self.timeout_central = None
        self.comando_pendente = None
        for botao in self.botoes_central:
            botao.state(["!disabled"])
        self.status_central.config(text=mensagem)

    def receber_resposta_central(self, dados):
        if self.comando_pendente is None:
            return
        numero, estado = self.comando_pendente
        if dados.get("caixa") != numero:
            return
        if dados.get("aceito") is True:
            if dados.get("estado") == estado:
                self.finalizar_comando(f"Caixa {numero} · {estado} registrado no backend.")
        else:
            self.finalizar_comando(dados.get("motivo") or "Comando recusado pelo backend.")

    def abrir_caixa(self, numero):

        if numero in self.janelas:
            self.janelas[numero].janela.lift()
            return

        caixa = JanelaCaixa(
            self.root,
            numero,
            self.mqtt,
            ao_fechar=lambda: self.remover_caixa(numero)
        )

        self.janelas[numero] = caixa

    def remover_caixa(self, numero):
        self.janelas.pop(numero, None)

    def processar_eventos(self):

        try:
            while True:

                evento = self.fila_eventos.get_nowait()

                tipo = evento["tipo"]

                if tipo == "conexao":

                    conectado = evento["conectado"]
                    mensagem = evento["mensagem"]

                    self.status.config(
                        text=mensagem,
                        foreground="green" if conectado else "red"
                    )

                elif tipo == "resposta_central":
                    self.receber_resposta_central(evento["dados"])

                elif tipo == "mensagem":

                    numero = evento["caixa"]
                    subtipo = evento["subtipo"]
                    dados = evento["dados"]

                    caixa = self.janelas.get(numero)

                    if caixa is None:
                        continue

                    if subtipo == "comando":
                        caixa.receber_comando(dados)

                    elif subtipo == "resposta":
                        caixa.receber_resposta(dados)

                elif tipo == "erro":
                    print("Erro MQTT:", evento["mensagem"])

        except Empty:
            pass

        self.root.after(50, self.processar_eventos)

    def fechar(self):

        self.mqtt.desconectar()
        self.root.destroy()


if __name__ == "__main__":

    root = tk.Tk()
    app = Simulador(root)
    root.mainloop()
