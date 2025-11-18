import sys
import os
import time
import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError
from dotenv import load_dotenv

# tornar importações resilientes ao modo de execução (script direto ou módulo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    # preferencialmente importe pelo package (quando executado como módulo)
    from src.config import FILTROS, MENSAGEM, LIMITE_DIARIO
except Exception:
    try:
        # tentativa alternativa caso o pacote não seja resolvido
        from config import FILTROS, MENSAGEM, LIMITE_DIARIO
    except Exception:
        # último recurso: import relativo (quando usado como package)
        from .config import FILTROS, MENSAGEM, LIMITE_DIARIO

load_dotenv()
try:
    from src.helpers import save_page_dump
except Exception:
    try:
        from helpers import save_page_dump
    except Exception:
        try:
            from .helpers import save_page_dump
        except Exception:
            save_page_dump = None

async def extract_and_connect(email, password, limit=5):
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto('https://www.linkedin.com/login')
        await page.fill('input#username', email)
        await page.fill('input#password', password)
        await page.click('button[type=submit]')
        try:
            await page.wait_for_selector('input[placeholder="Pesquisar"]', timeout=30000)
        except PWTimeoutError:
            print('Aviso: timeout após login. Salvando HTML de login para análise.')
            try:
                html = await page.content()
                with open('login_page_dump.html', 'w', encoding='utf-8') as f:
                    f.write(html)
            except Exception as e:
                print('Falha ao salvar HTML de login:', e)
            # prossegue mesmo assim

        busca = f"{FILTROS['cargo']} {FILTROS['localizacao']}"
        url = f'https://www.linkedin.com/search/results/people/?keywords={busca}'
        await page.goto(url)

        # rolar
        for i in range(8):
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            await page.wait_for_timeout(1500)

        # tenta selecionar resultados
        try:
            await page.wait_for_selector('div[data-view-name="people-search-result"]', timeout=10000)
        except PWTimeoutError:
            print('Seletor principal não encontrado. Salvando HTML em page_search.html')
            html = await page.content()
            with open('page_search.html', 'w', encoding='utf-8') as f:
                f.write(html)
            await context.close()
            await browser.close()
            return

        items = await page.query_selector_all('div[data-view-name="people-search-result"]')
        print(f'Items encontrados: {len(items)}')

        extracted = []
        connected = []

        for item in items:
            if len(connected) >= limit:
                break
            try:
                name_el = await item.query_selector('a[data-view-name="search-result-lockup-title"]')
                name = (await name_el.inner_text()).strip() if name_el else None
                link = await name_el.get_attribute('href') if name_el else None
                if link and link.startswith('/'):
                    link = 'https://www.linkedin.com' + link
                print('Perfil encontrado:', name, link)
                extracted.append({'nome': name, 'link': link})

                # tenta encontrar botão conectar dentro do bloco
                connect_el = await item.query_selector('a:has-text("Conectar"), a[aria-label*="Convidar"], a:has-text("Convidar")')
                # se não encontrou, tenta abrir menu "Mais" dentro do bloco e procurar lá
                if not connect_el:
                    menu_btn = await item.query_selector('button[aria-label*="Mais"], button:has-text("Mais"), button[aria-label*="More actions"]')
                    if menu_btn:
                        try:
                            await menu_btn.scroll_into_view_if_needed()
                            await menu_btn.click(force=True)
                            await page.wait_for_timeout(500)
                            # procurar botão conectar no contexto da página (menu pode ser global)
                            connect_el = await page.query_selector('a:has-text("Conectar"), button:has-text("Conectar"), a[aria-label*="Convidar"], button:has-text("Convidar")')
                        except Exception:
                            connect_el = None

                if not connect_el:
                    print('Botão Conectar não disponível neste item, pulando.')
                    continue

                print(f'Tentando conectar em {name}...')
                # garantir que o elemento esteja visível: rolar para ele
                try:
                    await connect_el.scroll_into_view_if_needed()
                except Exception:
                    pass

                # tentar clique normal, depois forçado, depois via evaluate como fallback
                clicked = False
                try:
                    await connect_el.click(timeout=5000)
                    clicked = True
                except Exception:
                    try:
                        await connect_el.click(force=True, timeout=5000)
                        clicked = True
                    except Exception:
                        try:
                            await page.evaluate('(el) => el.click()', connect_el)
                            clicked = True
                        except Exception as e:
                            print('Erro ao clicar no botão Conectar (fallbacks falharam):', e)

                if not clicked:
                    print('Não foi possível clicar em Conectar, pulando este item.')
                    continue

                await page.wait_for_timeout(1000)

                # Se o elemento de conectar for um link para preload (ex.: /preload/search-custom-invite/...),
                # abra esse URL diretamente em nova aba e tente o fluxo de envio lá — costuma ser mais confiável.
                try:
                    try:
                        tag = await connect_el.evaluate('(el) => el.tagName.toLowerCase()')
                    except Exception:
                        tag = None
                    if tag == 'a':
                        href = await connect_el.get_attribute('href')
                        if href and href.startswith('/preload'):
                            try:
                                full = 'https://www.linkedin.com' + href
                                print('Abrindo preload link direto:', full)
                                new_page = await context.new_page()
                                await new_page.goto(full)
                                await new_page.wait_for_timeout(1500)
                                # tentar enviar sem nota ou com nota no new_page
                                send_btn = await new_page.query_selector('button:has-text("Enviar sem nota"), button:has-text("Send now"), button:has-text("Enviar agora")')
                                add_btn = await new_page.query_selector('button:has-text("Adicionar nota"), button:has-text("Add a note")')
                                if send_btn:
                                    try:
                                        await send_btn.click()
                                        print('Enviado sem nota via preload para', name)
                                        connected.append({'nome': name, 'link': link})
                                        await new_page.close()
                                        continue
                                    except Exception as e:
                                        print('Falha ao clicar send_btn no preload:', e)
                                if add_btn:
                                    try:
                                        await add_btn.click()
                                        await new_page.wait_for_timeout(500)
                                        textarea = await new_page.query_selector('textarea[name="message"], textarea[aria-label*="nota"], textarea')
                                        if textarea:
                                            await textarea.fill(MENSAGEM)
                                            send_btn2 = await new_page.query_selector('button:has-text("Enviar"), button:has-text("Send"), button:has-text("Enviar convite")')
                                            if send_btn2:
                                                await send_btn2.click()
                                                print('Mensagem enviada via preload para', name)
                                                connected.append({'nome': name, 'link': link})
                                                await new_page.close()
                                                continue
                                    except Exception as e:
                                        print('Erro no fluxo add note via preload:', e)
                                # se chegou aqui sem sucesso, salvar dump do preload page
                                try:
                                    ts = int(time.time())
                                    new_html = await new_page.content()
                                    with open(f'preload_dump_{ts}.html', 'w', encoding='utf-8') as pf:
                                        pf.write(new_html)
                                    await new_page.screenshot(path=f'preload_screenshot_{ts}.png', full_page=True)
                                    print(f'Preload dump salvo: preload_dump_{ts}.html e preload_screenshot_{ts}.png')
                                except Exception as dump_e:
                                    print('Falha ao salvar preload dump/screenshot:', dump_e)
                                await new_page.close()
                            except Exception as e:
                                print('Erro ao abrir preload link:', e)
                except Exception:
                    pass
                # tenta detectar modal/dialog com seletores mais genéricos e procurar botões dentro
                try:
                    await page.wait_for_timeout(500)
                    dialog_selector = 'div[role="dialog"], div[class*="send-invite"], div[id*="artdeco-modal-outlet"], div[class*="artdeco-modal"]'
                    dialog = None
                    try:
                        await page.wait_for_selector(dialog_selector, timeout=5000)
                        dialog = await page.query_selector(dialog_selector)
                    except Exception:
                        dialog = None

                    async def find_buttons_in(root_page):
                        send_btn = None
                        add_btn = None
                        try:
                            send_btn = await root_page.query_selector('button:has-text("Enviar sem nota"), button:has-text("Enviar sem mensagem"), button:has-text("Send now"), button:has-text("Enviar agora")')
                        except Exception:
                            send_btn = None
                        try:
                            add_btn = await root_page.query_selector('button:has-text("Adicionar nota"), button:has-text("Add a note"), button:has-text("Add a message")')
                        except Exception:
                            add_btn = None
                        return send_btn, add_btn

                    send_no_note_btn = None
                    add_note_btn = None
                    if dialog:
                        send_no_note_btn, add_note_btn = await find_buttons_in(dialog)
                    else:
                        # tentar procurar diretamente na página (algumas variações aparecem fora do diálogo)
                        send_no_note_btn, add_note_btn = await find_buttons_in(page)

                    if send_no_note_btn:
                        try:
                            await send_no_note_btn.click()
                            print('Enviado sem nota para', name)
                            connected.append({'nome': name, 'link': link})
                            await page.wait_for_timeout(500)
                            continue
                        except Exception as e:
                            print('Falha ao clicar em "Enviar sem nota":', e)

                    if add_note_btn:
                        try:
                            await add_note_btn.click()
                            await page.wait_for_timeout(500)
                            # procura por textarea dentro do diálogo ou na página
                            textarea = None
                            if dialog:
                                textarea = await dialog.query_selector('textarea[name="message"], textarea[aria-label*="nota"], textarea[aria-label*="message"], textarea')
                            if not textarea:
                                textarea = await page.query_selector('textarea[name="message"], textarea[aria-label*="nota"], textarea[aria-label*="message"], textarea')
                            if textarea:
                                await textarea.fill(MENSAGEM)
                                # procurar botão de envio no modal
                                send_btn = None
                                if dialog:
                                    send_btn = await dialog.query_selector('button:has-text("Enviar"), button:has-text("Enviar convite"), button:has-text("Send"), button:has-text("Enviar agora"), button:has-text("Send now")')
                                if not send_btn:
                                    send_btn = await page.query_selector('button:has-text("Enviar"), button:has-text("Enviar convite"), button:has-text("Send"), button:has-text("Enviar agora"), button:has-text("Send now")')
                                if send_btn:
                                    try:
                                        await send_btn.click()
                                        print('Mensagem enviada para', name)
                                        connected.append({'nome': name, 'link': link})
                                        continue
                                    except Exception as e:
                                        print('Erro ao clicar em enviar após adicionar nota:', e)
                                        # vai para fallback de abrir perfil
                                else:
                                    # dump para análise
                                    try:
                                        ts = int(time.time())
                                        modal_html = await page.content()
                                        with open(f'modal_dump_{ts}.html', 'w', encoding='utf-8') as mf:
                                            mf.write(modal_html)
                                        await page.screenshot(path=f'modal_screenshot_{ts}.png', full_page=True)
                                        print(f'Modal dump salvo: modal_dump_{ts}.html e modal_screenshot_{ts}.png')
                                    except Exception as dump_e:
                                        print('Falha ao salvar modal dump/screenshot:', dump_e)
                                    # vai para fallback de abrir perfil
                            else:
                                try:
                                    ts = int(time.time())
                                    modal_html = await page.content()
                                    with open(f'modal_dump_{ts}.html', 'w', encoding='utf-8') as mf:
                                        mf.write(modal_html)
                                    await page.screenshot(path=f'modal_screenshot_{ts}.png', full_page=True)
                                    print(f'Modal dump salvo: modal_dump_{ts}.html e modal_screenshot_{ts}.png')
                                except Exception as dump_e:
                                    print('Falha ao salvar modal dump/screenshot (no textarea):', dump_e)
                                # vai para fallback de abrir perfil
                        except Exception as e:
                            print('Falha no fluxo de adicionar nota:', e)

                    # se chegamos aqui sem sucesso nos botões, tentar abrir o perfil em nova aba e executar lá
                    try:
                        print('Tentando fallback: abrir perfil em nova aba para enviar convite...')
                        if not link:
                            print('Link do perfil não disponível; pulando.')
                            connected.append({'nome': name, 'link': link})
                            continue
                        new_page = await context.new_page()
                        await new_page.goto(link)
                        await new_page.wait_for_timeout(2000)
                        # procurar botão conectar na página de perfil
                        try:
                            # evitar wait_for_selector por vezes falhar quando existem múltiplos elementos
                            profile_selectors = (
                                'button:has-text("Conectar"), button:has-text("Connect"), a:has-text("Conectar"), a:has-text("Connect"), button[aria-label*="Convidar"], a[aria-label*="Convidar"]'
                            )
                            els = await new_page.query_selector_all(profile_selectors)
                            # também tente selecionar elementos da barra sticky do perfil
                            try:
                                sticky = await new_page.query_selector_all('button.pvs-sticky-header-profile-actions__action, div.pvs-sticky-header-profile-actions__action[role="button"], [role="button"][aria-label*="Convidar"]')
                                if sticky and len(sticky) > 0:
                                    # colocar sticky no início da lista para priorizar
                                    els = sticky + els
                            except Exception:
                                pass
                            if not els or len(els) == 0:
                                raise Exception('Nenhum elemento de conectar encontrado na página de perfil')
                            profile_connect = els[0]
                            try:
                                await profile_connect.scroll_into_view_if_needed()
                            except Exception:
                                pass
                            clicked = False
                            try:
                                await profile_connect.click(timeout=5000)
                                clicked = True
                            except Exception:
                                try:
                                    await profile_connect.click(force=True, timeout=5000)
                                    clicked = True
                                except Exception:
                                    try:
                                        # tente disparar um evento de clique mais robusto
                                        await new_page.evaluate('''(el) => {
                                            el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true, cancelable:true, view:window}));
                                            el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true, cancelable:true, view:window}));
                                            el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true, view:window}));
                                        }''', profile_connect)
                                        clicked = True
                                    except Exception:
                                        clicked = False
                            if not clicked:
                                raise Exception('Falha ao clicar no botão Conectar (todos os fallbacks falharam)')
                            await new_page.wait_for_timeout(800)
                            # repetir fluxo de modal no new_page
                            try:
                                try:
                                    await new_page.wait_for_selector(dialog_selector, timeout=4000)
                                    new_dialog = await new_page.query_selector(dialog_selector)
                                except Exception:
                                    new_dialog = None
                                send_no_note_btn = None
                                add_note_btn = None
                                if new_dialog:
                                    send_no_note_btn = await new_dialog.query_selector('button:has-text("Enviar sem nota"), button:has-text("Send now"), button:has-text("Enviar agora")')
                                    add_note_btn = await new_dialog.query_selector('button:has-text("Adicionar nota"), button:has-text("Add a note")')
                                else:
                                    send_no_note_btn = await new_page.query_selector('button:has-text("Enviar sem nota"), button:has-text("Send now"), button:has-text("Enviar agora")')
                                    add_note_btn = await new_page.query_selector('button:has-text("Adicionar nota"), button:has-text("Add a note")')

                                if send_no_note_btn:
                                    await send_no_note_btn.click()
                                    print('Enviado sem nota (via perfil) para', name)
                                    connected.append({'nome': name, 'link': link})
                                    await new_page.close()
                                    continue

                                if add_note_btn:
                                    await add_note_btn.click()
                                    await new_page.wait_for_timeout(500)
                                    textarea = await new_page.query_selector('textarea[name="message"], textarea[aria-label*="nota"], textarea')
                                    if textarea:
                                        await textarea.fill(MENSAGEM)
                                        send_btn = await new_page.query_selector('button:has-text("Enviar"), button:has-text("Enviar convite"), button:has-text("Send"), button:has-text("Enviar agora"), button:has-text("Send now")')
                                        if send_btn:
                                            await send_btn.click()
                                            print('Mensagem enviada (via perfil) para', name)
                                            connected.append({'nome': name, 'link': link})
                                            await new_page.close()
                                            continue
                                # se ainda não conseguiu, salvar dump do new_page
                                ts = int(time.time())
                                new_html = await new_page.content()
                                with open(f'profile_modal_dump_{ts}.html', 'w', encoding='utf-8') as pf:
                                    pf.write(new_html)
                                await new_page.screenshot(path=f'profile_modal_screenshot_{ts}.png', full_page=True)
                                print(f'Fallback profile dump salvo: profile_modal_dump_{ts}.html e profile_modal_screenshot_{ts}.png')
                                await new_page.close()
                                connected.append({'nome': name, 'link': link})
                            except Exception as e:
                                print('Erro no fluxo de invite via perfil:', e)
                                try:
                                    ts = int(time.time())
                                    new_html = await new_page.content()
                                    with open(f'profile_modal_dump_{ts}.html', 'w', encoding='utf-8') as pf:
                                        pf.write(new_html)
                                    await new_page.screenshot(path=f'profile_modal_screenshot_{ts}.png', full_page=True)
                                except Exception as dump_e:
                                    print('Falha ao salvar dump do perfil (exceção):', dump_e)
                                await new_page.close()
                                connected.append({'nome': name, 'link': link})
                        except Exception as e:
                            print('Não foi possível localizar botão Conectar na página de perfil:', e)
                            try:
                                ts = int(time.time())
                                page_html = await page.content()
                                with open(f'no_connect_btn_dump_{ts}.html', 'w', encoding='utf-8') as pf:
                                    pf.write(page_html)
                                await page.screenshot(path=f'no_connect_btn_screenshot_{ts}.png', full_page=True)
                            except Exception as dump_e:
                                print('Falha ao salvar dump (no_connect):', dump_e)
                            connected.append({'nome': name, 'link': link})
                    except Exception as e:
                        print('Fallback de abrir perfil falhou:', e)
                        connected.append({'nome': name, 'link': link})
                except Exception as e:
                    print('Erro no fluxo de envio de mensagem (catch externo):', e)
                except Exception as e:
                    print('Erro no fluxo de envio de mensagem (catch externo):', e)

            except Exception as e:
                print('Erro ao processar item:', e)

        # resumo
        print('\nResumo extração:')
        for e in extracted:
            print('-', e['nome'], e['link'])
        print('\nTotal extraídos:', len(extracted))
        print('\nTotal conectados:', len(connected))

        # salva resultados
        with open('extracted_profiles.txt', 'w', encoding='utf-8') as f:
            for e in extracted:
                f.write(f"{e['nome']} | {e['link']}\n")

        await context.close()
        await browser.close()


if __name__ == '__main__':
    EMAIL = os.getenv('LINKEDIN_EMAIL')
    PASSWORD = os.getenv('LINKEDIN_PASSWORD')
    limit_str = input('Quantas pessoas deseja conectar (max)? [default 5]: ')
    try:
        limit = int(limit_str)
    except Exception:
        limit = 5
    asyncio.run(extract_and_connect(EMAIL, PASSWORD, limit))
