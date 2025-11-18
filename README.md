**Projeto**
- **Nome:** PYTHON_Com_IA-Automacao_de_Newtworking_no_LinkedIn
- **Descrição:** Automação em Python que busca perfis no LinkedIn com base em filtros, aplica critérios de seleção, e tenta enviar convites de conexão com mensagem personalizada. O projeto utiliza Playwright (Chromium) para interação com a interface web e grava dumps/html + screenshots para diagnóstico.

**Status**
- Em desenvolvimento. Funcionalidades principais implementadas, mas ainda há fragilidades relacionadas às variações do DOM e proteções da própria plataforma LinkedIn.
- Nota do autor: O projeto ainda está em desenvolvimento e atualmente estou tendo problemas com o LinkedIn, o que pode afetar o funcionamento de algumas funcionalidades (por exemplo, envio de convites). Agradeço a compreensão e qualquer contribuição ou dump/screenshot para diagnóstico.

**Principais recursos**
- Buscar perfis por filtros configuráveis.
- Extrair nome e link do perfil e salvar em `extracted_profiles.txt`.
- Tentar enviar convite com mensagem personalizada (`src/config.py` -> `MENSAGEM`).
- Fallbacks robustos: scroll, clique forçado, evaluate-click, abertura do perfil, abertura do link `/preload/search-custom-invite`.
- Captura automática de dumps e screenshots (`modal_dump_*.html`, `modal_screenshot_*.png`, `profile_modal_dump_*.html`, etc.) para debugging.

**Limitações conhecidas**
- Variações frequentes do DOM do LinkedIn (classes, estruturas e textos) podem quebrar seletores.
- Proteções anti-bot e mecanismos de detecção podem limitar automação (recomenda-se uso responsável e supervisão humana).
- Textos de botões variam por idioma e região (ex.: "Conectar" / "Connect").
- Execução deve ser feita com cuidado — use limites baixos por execução e cheque os dumps quando houver falhas.

**Requisitos**
- Python 3.10+ (testado com 3.11)
- `pip` para instalar dependências
- Playwright browser install

**Instalação**
1. Crie/ative um ambiente virtual (opcional, recomendado):

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

2. Instale dependências:

```cmd
pip install -r requirements.txt
python -m playwright install
```

3. Crie um arquivo `.env` na raiz com credenciais (NUNCA comitar credenciais públicas):

```
LINKEDIN_EMAIL=seu_email@exemplo.com
LINKEDIN_PASSWORD=sua_senha
```

**Como rodar**
- Executar o script Playwright (modo rápido/teste):

```cmd
python src\playwright_automation.py
```

- Alternativa (executar como módulo):

```cmd
python -m src.playwright_automation
```

Ao rodar, informe o limite de convites por execução quando solicitado (recomendado começar com 1 ou 2).

**Arquivos gerados / logs úteis**
- `extracted_profiles.txt` — lista de perfis extraídos (nome | link).
- `linkedin_automation.db` — banco SQLite com tentativas (quando em uso pelo módulo `storage`).
- `modal_dump_*.html`, `modal_screenshot_*.png` — dump do DOM do modal e screenshot quando o fluxo falha.
- `profile_modal_dump_*.html`, `profile_modal_screenshot_*.png` — dumps gerados no fallback por perfil.
- `preload_dump_*.html`, `preload_screenshot_*.png` — dumps quando abrimos a rota `/preload`.

**Boas práticas / recomendações de execução**
- Rode em modo `headful` (janela visível) para reduzir detecção e poder intervir manualmente.
- Use delays e limites baixos (configurar `LIMITE_DIARIO` ou passar o limite na entrada).
- Se der erro em determinado perfil, envie os `*_dump_*.html` e screenshots para análise e ajuste de seletores.
- Não use para spam — respeite políticas do LinkedIn e privacidade das pessoas.

**Contribuição**
- Relate problemas abrindo uma issue com o dump e screenshot associados.
- Pull requests são bem-vindos — foco em: robustez de seletores, adaptação para múltiplos idiomas, testes, e abstração de fluxos.

**Sugestões futuras**
- Normalizar seletores por atributos estáveis (ex.: `data-*`), caso disponíveis.
- Adicionar testes unitários/integrados para as funções de parsing.
- Implementar modo `dry-run` que apenas extrai e não tenta conectar.

**Aviso legal/ética**
- Este projeto é educacional/experimental. Use com responsabilidade. Automação de interações deve respeitar os termos de uso do LinkedIn e as leis aplicáveis.


