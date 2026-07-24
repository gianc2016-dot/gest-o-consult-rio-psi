import base64
import hashlib
import sqlite3
from cryptography.fernet import Fernet

NOME_BANCO = 'consultorio.db'


def conectar():
  return sqlite3.connect(NOME_BANCO)


def gerar_chave_da_senha(senha_psicologa: str) -> bytes:
  """Gera uma chave de criptografia a partir da senha digitada."""
  key = hashlib.sha256(senha_psicologa.encode()).digest()
  return base64.urlsafe_b64encode(key)


def criptografar_texto(texto: str, senha: str) -> str:
  chave = gerar_chave_da_senha(senha)
  f = Fernet(chave)
  return f.encrypt(texto.encode()).decode('utf-8')


def descriptografar_texto(texto_cripto: str, senha: str) -> str:
  try:
    chave = gerar_chave_da_senha(senha)
    f = Fernet(chave)
    return f.decrypt(texto_cripto.encode()).decode('utf-8')
  except Exception:
    return None


def criar_tabelas():
  conn = conectar()
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            telefone TEXT,
            valor_sessao REAL
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paciente_id INTEGER,
            data_hora TEXT,
            status_pagamento TEXT DEFAULT 'Pendente',
            prontuario_criptografado TEXT,
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)

  conn.commit()
  conn.close()


def cadastrar_paciente(nome, telefone, valor_sessao):
  conn = conectar()
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO pacientes (nome, telefone, valor_sessao)
        VALUES (?, ?, ?)
    """,
      (nome, telefone, valor_sessao),
  )
  conn.commit()
  conn.close()


def listar_pacientes():
  conn = conectar()
  cursor = conn.cursor()
  cursor.execute('SELECT id, nome, telefone, valor_sessao FROM pacientes')
  pacientes = cursor.fetchall()
  conn.close()
  return pacientes


def agendar_consulta(paciente_id, data_hora, status_pagamento='Pendente'):
  conn = conectar()
  cursor = conn.cursor()
  cursor.execute(
      """
        INSERT INTO sessoes (paciente_id, data_hora, status_pagamento)
        VALUES (?, ?, ?)
    """,
      (paciente_id, data_hora, status_pagamento),
  )
  conn.commit()
  conn.close()


def listar_agendamentos():
  conn = conectar()
  cursor = conn.cursor()
  cursor.execute("""
        SELECT sessoes.id, pacientes.nome, sessoes.data_hora, sessoes.status_pagamento, pacientes.valor_sessao, sessoes.prontuario_criptografado
        FROM sessoes
        JOIN pacientes ON sessoes.paciente_id = pacientes.id
        ORDER BY sessoes.data_hora DESC
    """)
  agendamentos = cursor.fetchall()
  conn.close()
  return agendamentos


def salvar_prontuario(sessao_id, texto_anotacao, senha):
  texto_criptografado = criptografar_texto(texto_anotacao, senha)
  conn = conectar()
  cursor = conn.cursor()
  cursor.execute(
      """
        UPDATE sessoes 
        SET prontuario_criptografado = ?
        WHERE id = ?
    """,
      (texto_criptografado, sessao_id),
  )
  conn.commit()
  conn.close()


if __name__ == '__main__':
  criar_tabelas()