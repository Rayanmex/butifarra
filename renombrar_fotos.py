"""
Renombra las fotos de la carpeta 'fotos/' con prefijo del índice del expositor.
"""
import re
import shutil
import unicodedata
from pathlib import Path

import pandas as pd

# Cargar aliases
try:
    from core.management.commands.aliases_fotos import ALIASES_FOTOS
except ImportError:
    ALIASES_FOTOS = {}


def normalizar(texto):
    if texto is None:
        return ""
    if isinstance(texto, float) and pd.isna(texto):
        return ""
    texto = str(texto)
    texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto = re.sub(r'[^a-z0-9]+', '', texto.lower())
    return texto


def extraer_sufijo(filename):
    base = Path(filename).stem
    if ' - ' in base:
        return base.rsplit(' - ', 1)[-1].strip()
    return base.strip()


def construir_indice_expositores(excel_path):
    df = pd.read_excel(excel_path, header=0, engine='openpyxl')
    df.columns = [str(c).replace('<br>', '\n').strip() for c in df.columns]

    col_empresa = None
    col_expositor = None
    for c in df.columns:
        if c.startswith('Marca o nombre de la empresa'):
            col_empresa = c
        elif c.startswith('Nombre del expositor'):
            col_expositor = c

    indice = {}
    aliases = {}

    for i, row in df.iterrows():
        empresa = str(row[col_empresa]).strip() if col_empresa else ''
        expositor = str(row[col_expositor]).strip() if col_expositor else ''

        if empresa and empresa.lower() != 'nan':
            idx = i + 1
            indice[empresa] = idx
            aliases[normalizar(empresa)] = empresa
            if expositor and expositor.lower() != 'nan':
                aliases[normalizar(expositor)] = empresa

    return indice, aliases


def encontrar_empresa(sufijo_norm, aliases):
    """4 estrategias de match, de más específica a más flexible."""
    # 1) Alias exacto de fotos (dueños)
    if sufijo_norm in ALIASES_FOTOS:
        return ALIASES_FOTOS[sufijo_norm], "alias_foto"

    # 2) Alias exacto del Excel (empresa o expositor)
    if sufijo_norm in aliases:
        return aliases[sufijo_norm], "alias_excel"

    # 3) Match parcial contra aliases del Excel
    mejor_len = 0
    mejor = None
    for key, val in aliases.items():
        if len(key) >= 5 and (key in sufijo_norm or sufijo_norm in key):
            if len(key) > mejor_len:
                mejor_len = len(key)
                mejor = val
    if mejor:
        return mejor, "parcial_excel"

    # 4) Match parcial contra ALIASES_FOTOS
    for key, val in ALIASES_FOTOS.items():
        if len(key) >= 5 and (key in sufijo_norm or sufijo_norm in key):
            if len(key) > mejor_len:
                mejor_len = len(key)
                mejor = val
    if mejor:
        return mejor, "parcial_alias"

    return None, None


def main():
    excel_path = Path('formulario.xlsx')
    origen = Path('fotos')
    destino = Path('fotos_renombradas')

    destino.mkdir(exist_ok=True)

    indice, aliases = construir_indice_expositores(excel_path)
    print(f"📄 {len(indice)} expositores detectados en el Excel")
    print(f"🎯 {len(ALIASES_FOTOS)} aliases de fotos cargados\n")

    contador = {idx: 0 for idx in indice.values()}
    asignados = 0
    sin_match = []

    archivos = sorted([
        f for f in origen.iterdir()
        if f.is_file() and not f.name.startswith('.')
    ])

    for archivo in archivos:
        if archivo.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp', '.gif'):
            continue

        sufijo = extraer_sufijo(archivo.name)
        sufijo_norm = normalizar(sufijo)

        empresa, metodo = encontrar_empresa(sufijo_norm, aliases)

        if not empresa:
            sin_match.append(archivo.name)
            continue

        idx = indice[empresa]
        contador[idx] += 1
        numero = contador[idx]
        ext = archivo.suffix.lower()
        nuevo_nombre = f"{idx:02d}-{numero:03d}{ext}"
        nuevo_path = destino / nuevo_nombre

        shutil.copy2(archivo, nuevo_path)

        if numero <= 2:
            print(f"  ✔ [{metodo:15}] {archivo.name[:50]:<50} → {nuevo_nombre}")
        asignados += 1

    print(f"\n✅ Total copiadas: {asignados}")
    print(f"⚠️  Sin match: {len(sin_match)}")

    if sin_match:
        print("\nArchivos sin match:")
        for n in sin_match[:40]:
            print(f"   - {n}")
        if len(sin_match) > 40:
            print(f"   ... y {len(sin_match) - 40} más")

        with open('fotos_sin_match.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sin_match))
        print(f"\n📝 Lista completa en: fotos_sin_match.txt")


if __name__ == '__main__':
    main()