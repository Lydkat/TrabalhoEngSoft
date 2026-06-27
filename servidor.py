from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# Conexão parametrizada com as suas credenciais e banco correto
def conectar_banco():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="Evacach1009*", 
        database="postogem_db"
    )

# Executa as cargas de dados iniciais obrigatórias para evitar quebras de chaves estrangeiras
def inicializar_banco():
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute(
            "INSERT IGNORE INTO postos (id_posto, nome, endereco, cnpj) VALUES (1, 'Posto Fugaz S/A', 'Av. Principal, 1000', '12345678000199')"
        )
        cursor.execute(
            "INSERT IGNORE INTO bombas (id_bomba, id_posto, descricao, status) VALUES (1, 1, 'Bomba 1', 'livre')"
        )
        cursor.execute(
            "INSERT IGNORE INTO combustiveis (id_combustivel, nome, preco_fixo_litro) VALUES (1, 'Gasolina Comum', 5.890)"
        )
        cursor.execute(
            "INSERT IGNORE INTO formas_pagamento (id_forma, nome_forma) VALUES (1, 'PIX')"
        )
        cursor.execute(
            "INSERT IGNORE INTO formas_pagamento (id_forma, nome_forma) VALUES (2, 'Cartao')"
        )

        conexao.commit()
        cursor.close()
        conexao.close()
        print("--> Banco de dados verificado, tabelas de apoio carregadas com sucesso.")
    except Exception as e:
        print(f"--> Aviso de inicialização: {e}")


@app.route("/api/login", methods=["POST"])
def login():
    dados = request.json
    cpf_digitado = dados.get("cpf")
    senha_digitada = dados.get("senha")

    if not cpf_digitado or not senha_digitada:
        return jsonify({"sucesso": False, "mensagem": "Preencha CPF e Senha."}), 400

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(
            "SELECT id_cliente, nome, senha_hash FROM clientes WHERE cpf = %s",
            (cpf_digitado,),
        )
        usuario = cursor.fetchone()

        if usuario:
            if usuario["senha_hash"] == senha_digitada:
                cursor.close()
                conexao.close()
                return jsonify({
                    "sucesso": True,
                    "mensagem": f"Bem-vindo de volta, {usuario['nome']}!",
                    "id_cliente": usuario["id_cliente"],
                }), 200
            else:
                cursor.close()
                conexao.close()
                return jsonify({"sucesso": False, "mensagem": "Senha incorreta."}), 401
        else:
            email_gerado = f"{cpf_digitado}@autoposto.mock"
            nome_gerado = f"Motorista {cpf_digitado[:4]}"

            cursor.execute(
                "INSERT INTO clientes (nome, cpf, email, senha_hash) VALUES (%s, %s, %s, %s)",
                (nome_gerado, cpf_digitado, email_gerado, senha_digitada),
            )
            conexao.commit()

            novo_id = cursor.lastrowid
            cursor.close()
            conexao.close()

            return jsonify({
                "sucesso": True,
                "mensagem": "Novo perfil criado! Bem-vindo ao Posto Fugaz.",
                "id_cliente": novo_id,
            }), 200

    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro fatal: {str(e)}"}), 500


@app.route("/api/abastecer", methods=["POST"])
def criar_abastecimento():
    dados = request.json
    id_cliente = dados.get("id_cliente")
    valor = dados.get("valor")
    metodo = dados.get("metodo") # 'pix' ou 'cartao'

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        id_bomba = 1
        id_combustivel = 1
        preco_litro = 5.890
        qtd_litros = float(valor) / preco_litro
        
        # Mapeamento do ID baseado na tabela formas_pagamento
        forma_pag = 1 if metodo == "pix" else 2

        query = """
            INSERT INTO transacoes (
                id_cliente, id_bomba, id_combustivel, forma_pagamento_usada, 
                preco_litro_cobrado, quantidade_litros, valor_abastecimento, 
                status_pagamento, status_bomba
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pendente', 'aguardando_pagamento')
        """
        cursor.execute(
            query,
            (
                id_cliente,
                id_bomba,
                id_combustivel,
                forma_pag,
                preco_litro,
                qtd_litros,
                valor,
            ),
        )
        conexao.commit()

        id_transacao_criada = cursor.lastrowid
        cursor.close()
        conexao.close()

        return jsonify({
            "sucesso": True,
            "id_transacao": id_transacao_criada,
        }), 201

    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro: {str(e)}"}), 500


@app.route("/api/pagar", methods=["POST"])
def pagar_transacao():
    dados = request.json
    id_transacao = dados.get("id_transacao")

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        # Ajustado para usar id_transacao no singular
        cursor.execute(
            "UPDATE transacoes SET status_pagamento = 'aprovado', status_bomba = 'liberada', data_finalizacao = NOW() WHERE id_transacao = %s",
            (id_transacao,),
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        
        return jsonify({
            "sucesso": True,
            "mensagem": "Bomba liberada! Pode retirar o bico.",
        }), 200
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": str(e)}), 500


@app.route("/api/pagar-cartao", methods=["POST"])
def pagar_cartao():
    dados = request.json
    id_transacao = dados.get("id_transacao")
    tipo_cartao = dados.get("tipo")
    numero_cartao = dados.get("numero_cartao")

    ultimos_digitos = numero_cartao.split()[-1] if len(numero_cartao) > 4 else "0000"
    numero_mascarado = f"**** **** **** {ultimos_digitos}"

    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()

        cursor.execute(
            "UPDATE transacoes SET status_pagamento = 'aprovado', status_bomba = 'liberada', data_finalizacao = NOW() WHERE id_transacao = %s",
            (id_transacao,),
        )
        conexao.commit()
        cursor.close()
        conexao.close()
        
        return jsonify({
            "sucesso": True,
            "mensagem": f"Cartão de {tipo_cartao.upper()} ({numero_mascarado}) autorizado com sucesso! Bomba liberada.",
        }), 200
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": str(e)}), 500


if __name__ == "__main__":
    inicializar_banco()
    app.run(port=5000, debug=True)