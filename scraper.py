import time
from playwright.sync_api import sync_playwright

def buscar_leads_maps(termo_busca: str, max_resultados: int = 10) -> list[dict]:
    """
    Busca empresas no Google Maps pelo termo informado e retorna uma lista de dicionários.
    """
    leads = []

    with sync_playwright() as p:
        # Abre o navegador visível para acompanhamento (e ótimo para gravar vídeo de portfólio)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="pt-BR")
        page = context.new_page()

        url = f"https://www.google.com/maps/search/{termo_busca.replace(' ', '+')}"
        print(f"🔎 Acessando: {url}")
        page.goto(url, timeout=60000)

        # Aguarda o painel lateral de resultados carregar
        page.wait_for_selector('div[role="feed"]', timeout=15000)
        painel_resultados = page.locator('div[role="feed"]')

        # Rola o painel algumas vezes para carregar mais empresas
        for _ in range(3):
            painel_resultados.evaluate("el => el.scrollBy(0, 1000)")
            time.sleep(1.5)

        # Coleta os links de todas as empresas carregadas na lista
        cards = page.locator('div[role="feed"] a[href*="/maps/place/"]').all()
        print(f"📋 Encontrados {len(cards)} resultados iniciais. Extraindo até {max_resultados}...")

        urls_visitadas = set()

        for card in cards:
            if len(leads) >= max_resultados:
                break

            href = card.get_attribute("href")
            if not href or href in urls_visitadas:
                continue
            urls_visitadas.add(href)

            try:
                card.click()
                # Espera o painel específico da empresa abrir (o aria-label dele é o próprio nome da empresa!)
                time.sleep(1.5)

                # O painel principal de detalhes da empresa fica sempre no ÚLTIMO div[role="main"] aberto
                painel_empresa = page.locator('div[role="main"]').last

                # 1. Nome da empresa (ignora a etiqueta "Patrocinado" dos anúncios)
                nome = ""
                for h1 in painel_empresa.locator("h1").all():
                    texto_h1 = h1.inner_text().strip()
                    if texto_h1 and "Patrocinado" not in texto_h1 and "Sponsored" not in texto_h1:
                        nome = texto_h1
                        break

                if not nome:
                    continue

                # 2. Telefone
                telefone = "Não informado"
                btn_telefone = painel_empresa.locator('button[data-item-id^="phone:"]')
                if btn_telefone.count() > 0:
                    aria_tel = btn_telefone.first.get_attribute("aria-label") or ""
                    telefone = aria_tel.replace("Telefone:", "").strip()

                # 3. Website
                site = "Não possui site"
                link_site = painel_empresa.locator('a[data-item-id="authority"]')
                if link_site.count() > 0:
                    site = link_site.first.get_attribute("href") or "Não possui site"

                # 4. Nota / Avaliação (dentro do painel da empresa)
                nota = "Sem nota"
                span_nota = painel_empresa.locator('div.F7nice span[aria-hidden="true"]').first
                if span_nota.count() > 0:
                    nota = span_nota.inner_text().strip()

                lead = {
                    "nome": nome,
                    "telefone": telefone,
                    "site": site,
                    "nota": nota
                }
                leads.append(lead)
                print(f"✅ [{len(leads)}/{max_resultados}] {nome} | Tel: {telefone} | Site: {site}")

            except Exception as e:
                print(f"⚠️ Erro ao extrair um card, pulando... ({e})")
                continue

        browser.close()

    return leads


if __name__ == "__main__":
    # Teste rápido rodando direto este arquivo
    resultados = buscar_leads_maps("Clínica Odontológica em Goiânia", max_resultados=5)
    print("\n--- RESUMO DA EXTRAÇÃO ---")
    for r in resultados:
        print(r)