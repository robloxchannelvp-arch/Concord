import os
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chave_secreta_concord_amigos"

USUARIOS_FILE = "usuarios.json"
MENSAGENS_FILE = "mensagens.json"

# --- FUNÇÕES DE LEITURA E ESCRITA EM ARQUIVOS TXT/JSON ---
def carregar_dados(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        return []
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_dados(caminho_arquivo, dados):
    with open(caminho_arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


# --- ROTAS PRINCIPAIS ---

@app.route("/")
def index():
    if "usuario_id" in session:
        return redirect(url_for("concord"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html") # Se tiver a tela de login

    email = request.form.get("email")
    senha = request.form.get("senha")

    usuarios = carregar_dados(USUARIOS_FILE)

    for u in usuarios:
        if u["email"] == email and check_password_hash(u["senha"], senha):
            session["usuario_id"] = u["id"]
            session["usuario_nome"] = u["nome"]
            session["usuario_foto"] = u.get("foto_perfil", "https://cdn.discordapp.com/embed/avatars/0.png")
            return redirect(url_for("concord"))

    return "E-mail ou senha incorretos!", 400


@app.route("/cadastrar", methods=["POST"])
def cadastrar():
    nome = request.form.get("nome")
    email = request.form.get("email")
    senha = request.form.get("senha")

    usuarios = carregar_dados(USUARIOS_FILE)

    # Verifica se e-mail já existe
    for u in usuarios:
        if u["email"] == email:
            return "Este e-mail já está cadastrado!", 400

    # Criptografa a senha por segurança
    senha_hash = generate_password_hash(senha)

    novo_usuario = {
        "id": len(usuarios) + 1,
        "nome": nome,
        "email": email,
        "senha": senha_hash,
        "foto_perfil": "https://cdn.discordapp.com/embed/avatars/0.png"
    }

    usuarios.append(novo_usuario)
    salvar_dados(USUARIOS_FILE, usuarios)

    return redirect(url_for("login"))


@app.route("/concord")
def concord():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuarios = carregar_dados(USUARIOS_FILE)
    mensagens = carregar_dados(MENSAGENS_FILE)

    usuario_atual = {
        "id": session.get("usuario_id"),
        "nome": session.get("usuario_nome"),
        "foto_perfil": session.get("usuario_foto")
    }

    # Passa o usuário logado, lista de mensagens e lista de membros para o HTML
    return render_template(
        "concord.html", 
        usuario=usuario_atual, 
        mensagens=mensagens, 
        membros=usuarios
    )


@app.route("/enviar_mensagem", methods=["POST"])
def enviar_mensagem():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    texto = request.form.get("mensagem")
    if not texto or texto.strip() == "":
        return redirect(url_for("concord"))

    mensagens = carregar_dados(MENSAGENS_FILE)

    horario = datetime.now().strftime("%H:%M")

    nova_msg = {
        "autor_nome": session.get("usuario_nome"),
        "autor_foto": session.get("usuario_foto"),
        "conteudo": texto,
        "data_envio": f"Hoje às {horario}"
    }

    mensagens.append(nova_msg)
    salvar_dados(MENSAGENS_FILE, mensagens)

    return redirect(url_for("concord"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ROTA PARA ABRIR A TELA DE PERFIL
@app.route("/perfil")
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    usuarios = carregar_dados(USUARIOS_FILE)
    usuario_atual = None
    
    for u in usuarios:
        if u["id"] == session["usuario_id"]:
            usuario_atual = u
            break

    return render_template("perfil.html", usuario=usuario_atual)


# ROTA PARA SALVAR AS ALTERAÇÕES DO PERFIL
@app.route("/salvar_perfil", methods=["POST"])
def salvar_perfil():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    novo_nome = request.form.get("nome")
    nova_foto = request.form.get("foto_perfil")

    usuarios = carregar_dados(USUARIOS_FILE)

    for u in usuarios:
        if u["id"] == session["usuario_id"]:
            u["nome"] = novo_nome
            u["foto_perfil"] = nova_foto
            session["usuario_nome"] = novo_nome
            session["usuario_foto"] = nova_foto
            break

    salvar_dados(USUARIOS_FILE, usuarios)

    return redirect(url_for("concord"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)