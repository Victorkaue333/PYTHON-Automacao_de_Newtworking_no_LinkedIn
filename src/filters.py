from .config import FILTROS

def filtrar_perfis(perfis):
    filtrados = []
    for perfil in perfis:
        # Aqui pode-se adicionar lógica para filtrar por empresa, nível, palavras-chave, etc.
        if FILTROS['palavras_chave']:
            if not any(palavra.lower() in perfil['nome'].lower() for palavra in FILTROS['palavras_chave']):
                continue
        filtrados.append(perfil)
    return filtrados
