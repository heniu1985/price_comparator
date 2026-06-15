from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from playwright.sync_api import sync_playwright

url = "https://www.mediaexpert.pl/komputery-i-tablety/dyski-i-pamieci/dyski-wewnetrzne/dysk-ssd-samsung-portable-touch-t7-1tbb-usb-3-2-gen-2-mu-pc1t0t-ww-grey"

# Generujemy losowy, prawdziwy User-Agent (np. z najnowszego Chrome)
ua = UserAgent(os="windows", browsers=["chrome"])
user_agent_string = ua.random

with sync_playwright() as p:
    # Uruchamiamy przeglądarkę z dodatkowymi argumentami ignorującymi proste testy bota
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",  # Wyłącza flagę webdriver
            "--no-sandbox",
            "--disable-infobars",
        ],
    )

    # Tworzymy nowy kontekst przeglądarki z niestandardowym User-Agent i innymi ustawieniami
    context = browser.new_context(
        user_agent=user_agent_string,
        viewport={"width": 1920, "height": 1080},
        locale="pl-PL",
        timezone_id="Europe/Warsaw",
    )

    page = context.new_page()

    # Dodajemy skrypt inicjalizacyjny, który nadpisuje właściwość navigator.webdriver, aby wyglądało to tak, jakbyśmy nie byli botem
    page.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    try:
        page.goto(url, wait_until="commit", timeout=20000)

        # Obsługa banera cookies (RODO)
        try:
            print("Próbuję zamknąć baner cookies (RODO)...")
            page.wait_for_selector(
                'button:has-text("ZAAKCEPTUJ WSZYSTKIE")',
                state="visible",
                timeout=2000,
            )
            page.click('button:has-text("ZAAKCEPTUJ WSZYSTKIE")')
            print("Baner cookies kliknięty.")
        except Exception:
            print(
                "Baner RODO nie pojawił się lub ma inną strukturę – pomijam."
            )

        print("Czekam na obecność ceny w kodzie strony...")

        page.wait_for_selector("span.whole", state="attached", timeout=10000)

        html_content = page.content()

    except Exception as e:
        print(f"\n[KRYTYCZNY BŁĄD] Nie udało się pobrać ceny. Szczegóły: {e}")
        print("Zapisuję zrzut ekranu jako 'error_page_v4.png'...")
        page.screenshot(path="error_page_v4.png")
        html_content = None

    context.close()
    browser.close()

if html_content:
    soup = BeautifulSoup(html_content, "html.parser")
    whole_span = soup.find("span", class_="whole")
    cents_span = soup.find("span", class_="cents")

    if whole_span and cents_span:
        zlote = whole_span.text.strip().replace(" ", "")
        grosze = cents_span.text.strip()
        cena = float(f"{zlote}.{grosze}")
        print(f"\nSukces! Cena to: {cena} zł")
    else:
        print("Nie dopasowano elementów w BeautifulSoup.")