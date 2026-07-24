import hashlib
import re
import sqlite3
import urllib.parse
import streamlit as st


# ==========================================
# 1. BANCO DE DADOS E CRIPTOGRAFIA
# ==========================================
def gerhar_hash_senha(senha):
  """Criptografa a senha do usuário usando SHA-256"""
  return hashlib.sha256(senha.encode()).hexdigest()


def conectar():
  return sqlite3.connect("consultorio.db")


def criar_tabelas():
  conn = conectar()
  c = conn.cursor()

  # Tabela de Usuários (Profissionais)
  c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

  # Tabela de Pacientes (com usuario_id para isolamento)
  c.execute("""
        CREATE TABLE IF NOT EXISTS pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            telefone TEXT,
            email TEXT,
            cpf TEXT,
            data_nascimento DATE,
            profissao TEXT,
            contato_emergencia TEXT,
            observacoes TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    """)

  # Tabela de Consultas (com usuario_id)
  c.execute("""
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            paciente_id INTEGER,
            data DATE,
            hora TIME,
            status TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (paciente_id) REFERENCES pacientes (id)
        )
    """)

  conn.commit()
  conn.close()


# ==========================================
# 2. FUNÇÕES AUXILIARES DE FORMATAÇÃO
# ==========================================
def formatar_telefone(telefone):
  if not telefone:
    return ""
  digits = re.sub(r"\D", "", str(telefone))
  if len(digits) == 11:
    return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
  elif len(digits) == 10:
    return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
  return telefone


def limpar_telefone(telefone):
  if not telefone:
    return ""
  num = re.sub(r"\D", "", str(telefone))
  if len(num) in [10, 11] and not num.startswith("55"):
    num = "55" + num
  return num


# ==========================================
# 3. CONFIGURAÇÃO E ESTILO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Sistema de Gestão - Psicologia", page_icon="🌿", layout="wide"
)

criar_tabelas()

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
        background-color: #f0fdf4 !important;
        color: #1e293b;
    }
    
    h1 { font-size: 26px !important; color: #0f172a !important; font-weight: 700; }
    h2, h3, h4 { color: #166534 !important; font-weight: 600; }

    div[data-baseweb="tab-list"] {
        background-color: #dcfce7;
        border-radius: 10px;
        padding: 4px;
    }
    
    button[data-baseweb="tab"] {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #166534 !important;
        border-radius: 8px;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        border: 1px solid #bbf7d0 !important;
    }

    div.stButton > button:first-child {
        background-color: #16a34a !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    
    .btn-whatsapp {
        display: inline-block;
        background-color: #25d366;
        color: white !important;
        font-weight: 600;
        padding: 8px 16px;
        border-radius: 8px;
        text-decoration: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Inicializa variável de sessão de login
if "usuario_logado" not in st.session_state:
  st.session_state["usuario_logado"] = None


# ==========================================
# 4. TELA DE LOGIN / CADASTRO
# ==========================================
def tela_login():
  st.title("🌿 Psicologia & Bem-Estar — Acesso ao Sistema")

  tab_login, tab_cadastro = st.tabs(
      ["🔑 Entrar no Sistema", "📝 Criar Nova Conta"]
  )

  with tab_login:
    st.subheader("Login do Profissional")
    with st.form("form_login"):
      email = st.text_input("E-mail")
      senha = st.text_input("Senha", type="password")
      btn_login = st.form_submit_button("Entrar")

      if btn_login:
        if email and senha:
          senha_hash = gerhar_hash_senha(senha)
          conn = conectar()
          c = conn.cursor()
          c.execute(
              "SELECT id, nome FROM usuarios WHERE email = ? AND senha = ?",
              (email, senha_hash),
          )
          user = c.fetchone()
          conn.close()

          if user:
            st.session_state["usuario_logado"] = {
                "id": user[0],
                "nome": user[1],
            }
            st.success(f"Bem-vindo(a), {user[1]}!")
            st.rerun()
          else:
            st.error("E-mail ou senha incorretos.")
        else:
          st.warning("Preencha todos os campos.")

  with tab_cadastro:
    st.subheader("Cadastro de Novo Profissional")
    with st.form("form_novo_usuario"):
      nome_novo = st.text_input("Nome Completo (ex: Dra. Heloísa Medeiros)")
      email_novo = st.text_input("E-mail Profissional")
      senha_nova = st.text_input("Crie uma Senha", type="password")
      btn_cadastrar = st.form_submit_button("Cadastrar Conta")

      if btn_cadastrar:
        if nome_novo and email_novo and senha_nova:
          senha_hash = gerhar_hash_senha(senha_nova)
          try:
            conn = conectar()
            c = conn.cursor()
            c.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome_novo, email_novo, senha_hash),
            )
            conn.commit()
            conn.close()
            st.success("Conta criada com sucesso! Faça login para acessar.")
          except sqlite3.IntegrityError:
            st.error("Este e-mail já está cadastrado no sistema.")
        else:
          st.warning("Preencha todos os campos obrigatórios.")


# ==========================================
# 5. SISTEMA PRINCIPAL (APÓS LOGIN)
# ==========================================
def sistema_principal():
  user_id = st.session_state["usuario_logado"]["id"]
  user_nome = st.session_state["usuario_logado"]["nome"]

  # Barra Lateral (Sidebar) com Informações do Usuário Logado
  st.sidebar.title(f"👤 {user_nome}")
  st.sidebar.write("Painel Profissional")
  if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state["usuario_logado"] = None
    st.rerun()

  st.title(f"🌿 Painel da {user_nome}")

  aba_inicio, aba_lista, aba_cadastro, aba_agenda = st.tabs([
      "🏠 Início",
      "📄 Pacientes",
      "➕ Novo Paciente",
      "📅 Agendar Consulta",
  ])

  # --- INÍCIO ---
  with aba_inicio:
    st.markdown("### 🌿 Cuidado, Escuta e Transformação")
    st.info(
        '> *"A ciência moderna ainda não produziu um medicamento tranquilizador'
        ' tão eficaz quanto o são umas poucas palavras bondosas."*\n    > **—'
        " Sigmund Freud**"
    )

  # --- FICHA DOS PACIENTES (FILTRADO PELO USUÁRIO LOGADO) ---
  with aba_lista:
    st.subheader("Seus Pacientes Cadastrados")

    conn = conectar()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, nome, telefone, email, cpf, data_nascimento, profissao, contato_emergencia, observacoes 
        FROM pacientes WHERE usuario_id = ? ORDER BY nome""",
        (user_id,),
    )
    pacientes = c.fetchall()
    conn.close()

    if pacientes:
      for p in pacientes:
        p_id, p_nome, p_tel, p_email, p_cpf, p_dt, p_prof, p_emerg, p_obs = p
        with st.expander(f"👤 {p_nome}"):
          col1, col2 = st.columns(2)
          with col1:
            st.write(f"**Telefone:** {p_tel or 'Não informado'}")
            st.write(f"**E-mail:** {p_email or 'Não informado'}")
            st.write(f"**CPF:** {p_cpf or 'Não informado'}")
          with col2:
            dt_br = (
                "/".join(reversed(p_dt.split("-"))) if p_dt else "Não informada"
            )
            st.write(f"**Data de Nascimento:** {dt_br}")
            st.write(f"**Profissão:** {p_prof or 'Não informada'}")
            st.write(
                f"**Contato de Emergência:** {p_emerg or 'Não informado'}"
            )

          if p_obs:
            st.markdown("---")
            st.write(f"**Observações:** {p_obs}")

          st.markdown("---")
          col_b1, col_b2 = st.columns(2)
          with col_b1:
            if st.button(f"✏️ Editar", key=f"edit_{p_id}"):
              st.session_state[f"editando_{p_id}"] = not st.session_state.get(
                  f"editando_{p_id}", False
              )
          with col_b2:
            if st.button(f"🗑️ Excluir", key=f"del_{p_id}"):
              conn = conectar()
              c = conn.cursor()
              c.execute(
                  "DELETE FROM pacientes WHERE id = ? AND usuario_id = ?",
                  (p_id, user_id),
              )
              conn.commit()
              conn.close()
              st.success("Paciente excluído!")
              st.rerun()
    else:
      st.info("Você ainda não tem pacientes cadastrados em sua conta.")

  # --- CADASTRO DE PACIENTE ---
  with aba_cadastro:
    st.subheader("Cadastrar Novo Paciente")
    with st.form("form_cadastrar_paciente"):
      nome = st.text_input("Nome Completo *")
      col_a, col_b = st.columns(2)
      with col_a:
        telefone_raw = st.text_input(
            "Telefone / WhatsApp", placeholder="(00) 00000-0000"
        )
        cpf = st.text_input("CPF")
      with col_b:
        email = st.text_input("E-mail")
        data_nasc = st.date_input(
            "Data de Nascimento", value=None, format="DD/MM/YYYY"
        )

      col_c, col_d = st.columns(2)
      with col_c:
        profissao = st.text_input("Profissão")
      with col_d:
        contato_emergencia_raw = st.text_input(
            "Contato de Emergência", placeholder="(00) 00000-0000"
        )

      observacoes = st.text_area("Observações / Histórico Inicial")
      submetido = st.form_submit_button("Salvar Paciente")

      if submetido:
        if nome.strip() != "":
          tel_fmt = formatar_telefone(telefone_raw)
          emerg_fmt = formatar_telefone(contato_emergencia_raw)

          conn = conectar()
          c = conn.cursor()
          c.execute(
              """
                    INSERT INTO pacientes (usuario_id, nome, telefone, email, cpf, data_nascimento, profissao, contato_emergencia, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
              (
                  user_id,
                  nome,
                  tel_fmt,
                  email,
                  cpf,
                  str(data_nasc) if data_nasc else "",
                  profissao,
                  emerg_fmt,
                  observacoes,
              ),
          )
          conn.commit()
          conn.close()
          st.success(f"Paciente **{nome}** cadastrado na sua conta!")
          st.rerun()
        else:
          st.error("O campo Nome é obrigatório.")

  # --- AGENDAMENTO ---
  with aba_agenda:
    st.subheader("📅 Agendamento de Consultas")
    conn = conectar()
    c = conn.cursor()
    c.execute(
        "SELECT id, nome, telefone FROM pacientes WHERE usuario_id = ? ORDER BY"
        " nome",
        (user_id,),
    )
    pacientes_lista = c.fetchall()
    conn.close()

    if not pacientes_lista:
      st.warning("Cadastre pacientes na sua conta antes de realizar agendamentos.")
    else:
      with st.form("form_agenda"):
        dict_pacientes = {f"{p[1]} ({p[2]})": (p[0], p[1], p[2]) for p in pacientes_lista}
        p_sel = st.selectbox("Selecione o Paciente", list(dict_pacientes.keys()))
        col_dt, col_hr = st.columns(2)
        with col_dt:
          dt_cons = st.date_input("Data da Consulta", format="DD/MM/YYYY")
        with col_hr:
          hr_cons = st.time_input("Horário")

        if st.form_submit_button("Agendar Consulta"):
          p_id, p_nome, p_tel = dict_pacientes[p_sel]
          conn = conectar()
          c = conn.cursor()
          c.execute(
              """
                        INSERT INTO consultas (usuario_id, paciente_id, data, hora, status)
                        VALUES (?, ?, ?, ?, ?)
                    """,
              (user_id, p_id, str(dt_cons), str(hr_cons), "Agendado"),
          )
          conn.commit()
          conn.close()
          st.success("Consulta agendada!")
          st.rerun()


# ==========================================
# 6. CONTROLE DE NAVEGAÇÃO
# ==========================================
if st.session_state["usuario_logado"] is None:
  tela_login()
else:
  sistema_principal()