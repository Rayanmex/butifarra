"""
Scraper del sitio oficial del 11º Festival de la Butifarra 2026.
URL: https://festivaldelabutifarra.jalpademendez.gob.mx/wp/
"""
import re
import json
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://festivaldelabutifarra.jalpademendez.gob.mx/wp/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def fetch(url=None):
    """Descarga el HTML del sitio (o de la URL alternativa)."""
    r = requests.get(url or BASE_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.text


def parse(html):
    """Extrae toda la información relevante del HTML."""
    soup = BeautifulSoup(html, "lxml")
    data = {"base_url": BASE_URL}

    # ---------- Meta ----------
    def meta(prop):
        tag = (soup.find("meta", attrs={"property": prop})
               or soup.find("meta", attrs={"name": prop}))
        return tag["content"] if tag and tag.has_attr("content") else None

    data["titulo"] = meta("og:title")
    data["descripcion"] = meta("og:description")
    data["imagen_principal"] = meta("og:image")

    # ---------- Carrusel del hero ----------
    data["carrusel_hero"] = [
        img.get("src")
        for img in soup.select(".elementor-image-carousel .swiper-slide img")
        if img.get("src")
    ]

    # ---------- Artistas (Cartelera) ----------
    artistas = []
    for h3 in soup.find_all("h3"):
        nombre = h3.get_text(strip=True)
        if not nombre or len(nombre) > 80:
            continue
        bloque = h3.find_parent("div", class_=re.compile(r"e-con"))
        if not bloque:
            continue
        img = bloque.find("img")
        texto = bloque.get_text(" ", strip=True)
        fecha = re.search(r"(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", texto, re.IGNORECASE)
        if fecha and img:
            artistas.append({
                "nombre": nombre,
                "cartel_url": img.get("src"),
                "dia_presentacion_texto": fecha.group(1),
            })
    data["artistas"] = artistas

    # ---------- Programa (3 días) ----------
    programa = []
    for h2 in soup.find_all("h2"):
        texto = h2.get_text(strip=True)
        m = re.match(r"(\d{1,2})\s+DE\s+(\w+)", texto, re.IGNORECASE)
        if m:
            bloque = h2.find_parent("div", class_=re.compile(r"e-con"))
            img = bloque.find("img") if bloque else None
            programa.append({
                "titulo": texto,
                "dia": int(m.group(1)),
                "mes": m.group(2).lower(),
                "imagen_url": img.get("src") if img else None,
            })
    data["programa"] = programa

    # ---------- Historia ----------
    historia = []
    h3_historia = soup.find("h3", string=re.compile("Historia del Festival", re.I))
    if h3_historia:
        contenedor = h3_historia.find_parent("div", class_=re.compile(r"e-con"))
        if contenedor:
            for p in contenedor.find_all("p"):
                txt = p.get_text(" ", strip=True)
                if txt and len(txt) > 20:
                    historia.append(txt)
    data["historia"] = historia

    # ---------- Galería de fotos ----------
    data["galeria_fotos"] = [
        a.get("href")
        for a in soup.select(".fg-thumb")
        if a.get("href")
    ]

    # ---------- Galería de videos ----------
    videos = []
    for video in soup.find_all("video"):
        src = video.get("src")
        if src:
            videos.append({
                "url": src,
                "poster": video.get("poster") or "",
            })
    data["galeria_videos"] = videos

    # ---------- Patrocinadores ----------
    data["patrocinadores_logos"] = [
        img.get("src")
        for img in soup.select(".elementor-image-gallery img")
        if img.get("src") and "logotipo" in img.get("src", "").lower()
    ]

    # ---------- Redes sociales ----------
    data["facebook_url"] = None
    data["instagram_url"] = None
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "facebook.com/FestivalDeLaButifarra" in href:
            data["facebook_url"] = href
        if "instagram.com/festivalbutifarra" in href:
            data["instagram_url"] = href

    return data


if __name__ == "__main__":
    datos = parse(fetch())
    with open("festival_2026.json", "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("✅ Guardado en festival_2026.json")