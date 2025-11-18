import asyncio
from playwright.async_api import async_playwright
import time
from .config import FILTROS, MENSAGEM, LIMITE_DIARIO
from .storage import init_db, perfil_ja_contactado, registrar_envio

# Script mínimo usando Playwright para login, busca e salvar HTML

async def login_and_search(playwright, email, password, busca):
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto('https://www.linkedin.com/login')
    await page.fill('input#username', email)
    await page.fill('input#password', password)
    await page.click('button[type=submit]')
    # Em vez de aguardar 'networkidle' (que pode não ocorrer), aguarda um seletor confiável
    try:
        await page.wait_for_selector('input[placeholder="Pesquisar"]', timeout=60000)
    except Exception:
        # Se timeout, salva screenshot e HTML para análise e tenta prosseguir
        try:
            await page.screenshot(path='login_timeout.png', full_page=True)
        except Exception:
            pass
        try:
            html = await page.content()
            with open('login_page_dump.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print('Timeout no login: HTML salvo em login_page_dump.html')
        except Exception as e:
            print(f'Erro ao salvar HTML de login: {e}')
    # navega para a página de pesquisa
    await page.goto(f'https://www.linkedin.com/search/results/people/?keywords={busca}')
    # espera até que resultados apareçam, ou salva HTML para análise
    try:
        await page.wait_for_selector('li.reusable-search__result-container, div.entity-result__item, div.search-result__info', timeout=60000)
    except Exception:
        try:
            await page.screenshot(path='search_timeout.png', full_page=True)
        except Exception:
            pass
        try:
            html = await page.content()
            with open('page_search.html', 'w', encoding='utf-8') as f:
                f.write(html)
            print('Seletor não encontrado: HTML salvo em page_search.html')
        except Exception as e:
            print(f'Erro ao salvar HTML da busca: {e}')
        return
    # rola a página algumas vezes para carregar resultados extras
    for i in range(5):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(2000)
    # salva o html para inspeção
    html = await page.content()
    with open('page_search.html', 'w', encoding='utf-8') as f:
        f.write(html)
    await context.close()
    await browser.close()

async def run(email, password):
    busca = f"{FILTROS['cargo']} {FILTROS['localizacao']}"
    async with async_playwright() as pw:
        await login_and_search(pw, email, password, busca)

if __name__ == '__main__':
    import os
    from dotenv import load_dotenv
    load_dotenv()
    EMAIL = os.getenv('LINKEDIN_EMAIL')
    PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    asyncio.run(run(EMAIL, PASSWORD))
