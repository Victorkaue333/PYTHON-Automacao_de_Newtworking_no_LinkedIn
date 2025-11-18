import os
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_EMAIL = os.getenv('LINKEDIN_EMAIL')
LINKEDIN_PASSWORD = os.getenv('LINKEDIN_PASSWORD')

# Filtros e mensagens podem ser carregados de um arquivo JSON/YAML
FILTROS = {
    'cargo': 'Python Developer',
    'localizacao': 'São Paulo',
    'empresa': None,
    'nivel': None,
    'palavras_chave': ['engenharia', 'recrutador']
}

MENSAGEM = "Estou aumentando a minha rede de networking no LinkedIn e assim desejo me conectar com você."

LIMITE_DIARIO = 20
DELAY_ENTRE_CONEXOES = 10  # segundos
