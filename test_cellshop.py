"""
Prueba de extracción de la lista de precios de Cellshop.

Uso:
    pip install playwright
    python -m playwright install chromium
    python test_cellshop.py

Primera prueba: abre Chromium visible para poder detectar si Cellshop muestra
una verificación de Cloudflare o requiere una sesión.
"""

from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

URL = "https://cellshop.com/listadeprecos"
OUTPUT = Path("cellshop_lista_precios.txt")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        print(f"Abriendo: {URL}")

        response = page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        print("HTTP:", response.status if response else "sin respuesta")

        try:
            page.locator("#listado").wait_for(state="attached", timeout=60000)
        except PlaywrightTimeoutError:
            title = page.title()
            body = page.locator("body").inner_text()[:2500]
            print("\nNo apareció la tabla #listado.")
            print("Título:", title)
            print("Texto visible de la página:\n", body)
            print(
                "\nSi aparece una verificación de Cloudflare, completala manualmente "
                "en la ventana del navegador y volvé a ejecutar el script."
            )
            browser.close()
            return

        table = page.locator("#listado")
        row_count = table.locator("tr").count()
        print(f"Filas encontradas (incluye encabezado): {row_count}")

        # Reproduce el formato de tableToTXT() del sitio.
        lines = [
            f"Lista de preços atualizada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} hs.\n"
        ]

        for i in range(1, row_count):
            cells = table.locator("tr").nth(i).locator("td")
            cell_count = cells.count()
            if cell_count < 4:
                continue

            parts = []

            # Columna 0: código, ancho 15.
            value = cells.nth(0).evaluate("(el) => el.innerHTML")
            parts.append(value)
            parts.append(" " * max(0, 15 - len(value)))

            # Columna 1: texto del primer span, hasta 95 caracteres;
            # el relleno se calcula usando la longitud original, como en el JS.
            span = cells.nth(1).locator("span").first
            value = span.evaluate("(el) => el.innerHTML") if span.count() else ""
            parts.append(value[:95])
            parts.append(" " * max(0, 100 - len(value)))

            # Columna 2: contenido HTML, hasta 40 caracteres; ancho 45.
            value = cells.nth(2).evaluate("(el) => el.innerHTML")
            parts.append(value[:40])
            parts.append(" " * max(0, 45 - len(value)))

            # Columna 3: precio.
            value = cells.nth(3).evaluate("(el) => el.innerHTML")
            parts.append(value)

            lines.append("".join(parts))

        OUTPUT.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nTXT guardado: {OUTPUT.resolve()}")
        print(f"Productos exportados: {len(lines) - 1}")
        print("\nMuestra de las primeras líneas:")
        print("\n".join(lines[:4]))

        browser.close()


if __name__ == "__main__":
    main()
