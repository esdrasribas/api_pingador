# AQUI VAMOS INCLUIR AS INTEGRAÇÕES DE BANCO COM O PORTALCGS
import pymysql
from pymysql.cursors import DictCursor
from pymysql import MySQLError
import logging
import os
from dotenv import load_dotenv
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
load_dotenv()


def conectar_ao_banco():
    try:
        connection = pymysql.connect(
            host=os.environ.get('DB_HOST_CGS'),
            user=os.environ.get('DB_USER_CGS'),
            password=os.environ.get('DB_PASSWORD_CGS'),
            database=os.environ.get('DB_NAME_CGS')
        )
        return connection
    except pymysql.MySQLError as e:
        print(f"Erro ao conectar no banco: {e}")

def busca_ip_cliente(circuito):
    connection = conectar_ao_banco()

    if connection:
        try:
            with connection.cursor(DictCursor) as cursor: 
                query = "SELECT designacao, loc, ccto, pe, ip_backbone, ip_cliente, descricao, modelo, produto FROM base_rtping_limpa_pingador WHERE designacao = %s and produto in('CN','VM') LIMIT 1"
                cursor.execute(query, (circuito))
                reparos = cursor.fetchone()
                if reparos:
                    return reparos
                else:
                    logging.info("[busca_ip_cliente] Nenhum IP retornado para o circuito")
                    return []
        except MySQLError as e:
            logging.error(f"Erro ao acessar o banco de dados: {e}")
        finally:
            connection.close()
    return []


# teste = busca_ip_cliente("SDR5024995")
# print(teste)