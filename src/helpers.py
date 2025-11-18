import time

async def save_page_dump(page, prefix='dump'):
    """Salva HTML e screenshot da página com prefixo e timestamp.
    Uso: await save_page_dump(page, 'modal')
    """
    try:
        ts = int(time.time())
        html = await page.content()
        fname_html = f"{prefix}_dump_{ts}.html"
        fname_png = f"{prefix}_screenshot_{ts}.png"
        with open(fname_html, 'w', encoding='utf-8') as f:
            f.write(html)
        await page.screenshot(path=fname_png, full_page=True)
        print(f"Dump salvo: {fname_html} e {fname_png}")
    except Exception as e:
        print('Falha ao salvar dump/screenshot:', e)
