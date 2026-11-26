import sqlite3
from contextlib import contextmanager

from .config import DATABASE_PATH


@contextmanager
def conectar():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(DATABASE_PATH, timeout=10)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexao
        conexao.commit()
    except Exception:
        conexao.rollback()
        raise
    finally:
        conexao.close()


def inicializar_banco():
    with conectar() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS caixas_cadastradas (
            numero_caixa TEXT PRIMARY KEY,
            ativa INTEGER NOT NULL DEFAULT 1,
            data_cadastro TEXT NOT NULL DEFAULT (datetime('now', '-3 hours'))
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS estados_caixas (
            numero_caixa TEXT PRIMARY KEY,
            estado TEXT NOT NULL DEFAULT 'NAO_USADA',
            data_hora TEXT NOT NULL DEFAULT (datetime('now', '-3 hours')),
            FOREIGN KEY (numero_caixa) REFERENCES caixas_cadastradas(numero_caixa)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS historico_caixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_caixa TEXT NOT NULL,
            status TEXT NOT NULL,
            data_hora TEXT NOT NULL DEFAULT (datetime('now', '-3 hours'))
        )""")
        # Em uma instalação nova, prepara as mesmas três caixas de demonstração.
        quantidade = db.execute("SELECT COUNT(*) FROM caixas_cadastradas").fetchone()[0]
        if quantidade == 0:
            for numero in ("01", "02", "03"):
                db.execute("INSERT OR IGNORE INTO caixas_cadastradas (numero_caixa) VALUES (?)", (numero,))
                db.execute("INSERT OR IGNORE INTO estados_caixas (numero_caixa, estado) VALUES (?, 'NAO_USADA')", (numero,))


def listar_caixas():
    with conectar() as db:
        rows = db.execute("""SELECT c.numero_caixa, c.ativa, c.data_cadastro,
            COALESCE(e.estado, 'SEM_ESTADO') AS estado, e.data_hora
            FROM caixas_cadastradas c LEFT JOIN estados_caixas e
            ON e.numero_caixa = c.numero_caixa ORDER BY c.numero_caixa""").fetchall()
        return [dict(r) for r in rows]


def obter_caixa(numero):
    with conectar() as db:
        row = db.execute("""SELECT c.numero_caixa, c.ativa, c.data_cadastro,
            COALESCE(e.estado, 'SEM_ESTADO') AS estado, e.data_hora
            FROM caixas_cadastradas c LEFT JOIN estados_caixas e
            ON e.numero_caixa = c.numero_caixa WHERE c.numero_caixa = ?""", (numero,)).fetchone()
        return dict(row) if row else None


def listar_historico(numero=None, limite=200):
    with conectar() as db:
        if numero:
            rows = db.execute("SELECT * FROM historico_caixas WHERE numero_caixa = ? ORDER BY id DESC LIMIT ?", (numero, limite)).fetchall()
        else:
            rows = db.execute("SELECT * FROM historico_caixas ORDER BY id DESC LIMIT ?", (limite,)).fetchall()
        return [dict(r) for r in rows]


def caixa_ativa(numero):
    with conectar() as db:
        row = db.execute("SELECT numero_caixa FROM caixas_cadastradas WHERE numero_caixa = ? AND ativa = 1", (numero,)).fetchone()
        return row is not None


def atualizar_estado(numero, estado):
    with conectar() as db:
        db.execute("""INSERT INTO estados_caixas (numero_caixa, estado, data_hora)
            VALUES (?, ?, datetime('now', '-3 hours'))
            ON CONFLICT(numero_caixa) DO UPDATE SET
            estado=excluded.estado, data_hora=excluded.data_hora""", (numero, estado))
        db.execute("INSERT INTO historico_caixas (numero_caixa, status, data_hora) VALUES (?, ?, datetime('now', '-3 hours'))", (numero, estado))


def cadastrar_caixa(numero):
    with conectar() as db:
        db.execute("INSERT INTO caixas_cadastradas (numero_caixa, ativa) VALUES (?, 1)", (numero,))
        db.execute("INSERT INTO estados_caixas (numero_caixa, estado) VALUES (?, 'NAO_USADA')", (numero,))


def definir_ativa(numero, ativa):
    with conectar() as db:
        cur = db.execute("UPDATE caixas_cadastradas SET ativa = ? WHERE numero_caixa = ?", (1 if ativa else 0, numero))
        return cur.rowcount > 0


def liberar_se_pronta(numero):
    with conectar() as db:
        row = db.execute("""SELECT c.ativa, e.estado FROM caixas_cadastradas c
            LEFT JOIN estados_caixas e ON e.numero_caixa=c.numero_caixa
            WHERE c.numero_caixa=?""", (numero,)).fetchone()
        if row is None:
            return False, "Caixa não cadastrada", None
        if row["ativa"] != 1:
            return False, "Caixa desativada", row["estado"]
        if row["estado"] != "PRONTO":
            return False, "A caixa só pode ser liberada quando estiver PRONTO", row["estado"] or "SEM_ESTADO"
        db.execute("UPDATE estados_caixas SET estado='NAO_USADA', data_hora=datetime('now', '-3 hours') WHERE numero_caixa=? AND estado='PRONTO'", (numero,))
        db.execute("INSERT INTO historico_caixas (numero_caixa, status, data_hora) VALUES (?, 'NAO_USADA', datetime('now', '-3 hours'))", (numero,))
        return True, "CAIXA LIBERADA", "NAO_USADA"
