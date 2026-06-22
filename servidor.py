from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)  


def conectar_banco():
    return mysql.connector.connect(
        host="localhost",
        user="root",          
        password="",  
        database="postog2"      
    )


@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    cpf_digitado = dados.get('cpf')
    senha_digitada = dados.get('senha')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor(dictionary=True)
        
    
        query = "SELECT id_cliente, nome, senha_hash FROM clientes WHERE cpf = %s"
        cursor.execute(query, (cpf_digitado,))
        usuario = cursor.fetchone()
        
        cursor.close()
        conexao.close()
        
        if usuario and usuario['senha_hash'] == senha_digitada:
            return jsonify({
                "sucesso": True, 
                "mensagem": f"Bem-vindo, {usuario['nome']}!",
                "id_cliente": usuario['id_cliente']
            }), 200
        else:
            return jsonify({"sucesso": False, "mensagem": "CPF ou senha incorretos."}), 401
            
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro no banco: {str(e)}"}), 500


@app.route('/api/abastecer', methods=['POST'])
def criar_abastecimento():
    dados = request.json
    id_cliente = dados.get('id_cliente')
    valor = dados.get('valor')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        
        id_bomba_teste = 1
       
        forma_pagamento_teste = 1
        
       
        query = """
            INSERT INTO transacoes (id_cliente, id_bomba, forma_pagamento_usada, valor_abastecimento, status_pagamento, status_bomba)
            VALUES (%s, %s, %s, %s, 'pendente', 'aguardando_pagamento')
        """
        cursor.execute(query, (id_cliente, id_bomba_teste, forma_pagamento_teste, valor))
        conexao.commit()
        
        id_transacao_criada = cursor.lastrowid
        
        cursor.close()
        conexao.close()
        
        return jsonify({
            "sucesso": True,
            "mensagem": "Transação gerada! Aguardando pagamento.",
            "id_transacao": id_transacao_criada
        }), 201
        
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro ao registrar abastecimento: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)


@app.route('/api/pagar', methods=['POST'])
def pagar_transacao():
    dados = request.json
    id_transacao = dados.get('id_transacao')
    
    try:
        conexao = conectar_banco()
        cursor = conexao.cursor()
        
        query = """
            UPDATE transacoes 
            SET status_pagamento = 'aprovado', 
                status_bomba = 'liberada',
                data_finalizacao = NOW()
            WHERE id_transacoes = %s
        """
        cursor.execute(query, (id_transacao,))
        conexao.commit()
        
        cursor.close()
        conexao.close()
        
        return jsonify({
            "sucesso": True,
            "mensagem": "Pagamento aprovado com sucesso! Bomba liberada para abastecimento."
        }), 200
        
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro ao processar pagamento: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)