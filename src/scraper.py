from selenium.webdriver.common.by import By
import time
from .config import FILTROS

def buscar_perfis(driver):
    # Exemplo: busca por cargo e localização
    busca = f"{FILTROS['cargo']} {FILTROS['localizacao']}"
    driver.get(f'https://www.linkedin.com/search/results/people/?keywords={busca}')
    print("Aguardando carregamento da página de busca...")
    time.sleep(8)
    # Rola a página várias vezes para tentar carregar mais perfis
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        print(f"Rolagem {i+1}/5 realizada.")
    # Tenta múltiplos seletores para garantir que encontra os perfis
    seletores = [
        'li.reusable-search__result-container',
        'div.entity-result__item',
        'div.search-result__info'
    ]
    perfis = []
    for seletor in seletores:
        encontrados = driver.find_elements(By.CSS_SELECTOR, seletor)
        print(f"Perfis encontrados com seletor '{seletor}': {len(encontrados)}")
        if len(encontrados) > 0:
            perfis = encontrados
            break
    if not perfis:
        print("Nenhum perfil encontrado. Verifique se o LinkedIn mudou a estrutura da página ou se há bloqueio para automação.")
        # Salva o HTML atual para análise manual
        try:
            with open('search_page_dump.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            print('HTML salvo em search_page_dump.html para inspeção.')
        except Exception as e:
            print(f'Erro ao salvar HTML da página: {e}')
    resultados = []
    for perfil in perfis:
        try:
            link_elem = perfil.find_element(By.CSS_SELECTOR, 'a.app-aware-link[href*="/in/"]')
            link = link_elem.get_attribute('href')
            nome_elem = perfil.find_element(By.CSS_SELECTOR, 'span[aria-hidden="true"]')
            nome = nome_elem.text.strip()
            if nome and link:
                print(f"Perfil extraído: {nome} | {link}")
                resultados.append({'nome': nome, 'link': link})
        except Exception as e:
            print(f"Erro ao extrair perfil: {e}")
    print(f"Perfis extraídos: {len(resultados)}")
    return resultados
