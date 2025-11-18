
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.auth import linkedin_login
from src.scraper import buscar_perfis
from src.filters import filtrar_perfis
from src.interact import enviar_conexao
from src.storage import init_db, perfil_ja_contactado, registrar_envio


def main():
    init_db()
    options = Options()
    options.add_argument('--start-maximized')
    # Garante que não está em modo headless
    # options.add_argument('--headless')  # NÃO usar headless
    # Altera o user-agent para simular acesso humano
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(options=options)
    try:
        if not linkedin_login(driver):
            print('Falha no login.')
            return
        try:
            limite = int(input("Quantas pessoas você deseja se conectar? "))
        except ValueError:
            print("Valor inválido. Usando 5 como padrão.")
            limite = 5
        perfis = buscar_perfis(driver)
        print(f"Título da página após busca: {driver.title}")
        time.sleep(5)  # Delay extra para garantir carregamento
        perfis_filtrados = filtrar_perfis(perfis)
        conectados = []
        for perfil in perfis_filtrados:
            if len(conectados) >= limite:
                break
            if not perfil_ja_contactado(perfil['link']):
                sucesso = enviar_conexao(driver, perfil)
                if sucesso:
                    registrar_envio(perfil)
                    conectados.append(perfil)
                    print(f"Conexão enviada para: {perfil['nome']}")
                else:
                    print(f"Falha ao enviar para: {perfil['nome']}")
            else:
                print(f"Já contactado: {perfil['nome']}")
        print("\nResumo das conexões realizadas:")
        for p in conectados:
            print(f"- {p['nome']} | {p['link']}")
        print(f"\nTotal de conexões realizadas: {len(conectados)}")
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
