import time
from .config import MENSAGEM, DELAY_ENTRE_CONEXOES

def enviar_conexao(driver, perfil):
    driver.get(perfil['link'])
    time.sleep(2)
    # Rola a página para garantir que todos os botões carreguem
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)
    try:
        # Tenta encontrar o botão "Conectar" por diferentes métodos
        botao_conectar = None
        # 1. Por aria-label
        try:
            botao_conectar = driver.find_element('xpath', "//button[contains(@aria-label, 'Conectar')]")
        except:
            pass
        # 2. Por texto visível
        if not botao_conectar:
            try:
                botao_conectar = driver.find_element('xpath', "//button[normalize-space(text())='Conectar']")
            except:
                pass
        # 3. Por outros possíveis textos (variações)
        if not botao_conectar:
            try:
                botoes = driver.find_elements('tag name', 'button')
                for botao in botoes:
                    if 'conectar' in botao.text.lower() and botao.is_displayed() and botao.is_enabled():
                        botao_conectar = botao
                        break
            except:
                pass
        if not botao_conectar:
            print(f"Botão 'Conectar' não encontrado para {perfil['nome']} - {perfil['link']}")
            return False
        print(f"Clicando em 'Conectar' para {perfil['nome']}")
        botao_conectar.click()
        time.sleep(1)
        # Tenta adicionar nota/mensagem
        try:
            adicionar_nota = driver.find_element('xpath', "//button[contains(@aria-label, 'Adicionar nota') or contains(text(), 'Adicionar nota')]")
            adicionar_nota.click()
            campo_mensagem = driver.find_element('xpath', "//textarea[@name='message']")
            campo_mensagem.send_keys(MENSAGEM)
            enviar = driver.find_element('xpath', "//button[contains(@aria-label, 'Enviar agora') or contains(text(), 'Enviar')]")
            enviar.click()
            print(f"Mensagem enviada para {perfil['nome']}")
        except Exception as e:
            print(f"Não foi possível adicionar mensagem personalizada para {perfil['nome']}: {e}")
            return False
        time.sleep(DELAY_ENTRE_CONEXOES)
        return True
    except Exception as e:
        print(f"Erro ao enviar conexão para {perfil['nome']}: {e}")
        return False
