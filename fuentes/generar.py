#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera la web completa a partir del PDF de la edición docente.

    python fuentes/generar.py  documento.pdf  [carpeta_de_salida]
    python fuentes/generar.py  documento.docx [carpeta_de_salida]     (necesita LibreOffice instalado)

Sin carpeta de salida escribe junto a la carpeta «fuentes», es decir, en la raíz de la web.

Lee del propio PDF los títulos, la autoría, qué momentos son de elaboración propia y cuáles siguen pendientes; localiza dónde
empieza y acaba cada momento; guarda cada página como imagen (paginas/NNN.webp) y escribe
index.html. La web muestra recortes de esas imágenes: el trabajo se ve tal como está maquetado.

Las aportaciones que aún no están en el PDF se dejan, también en PDF, en la carpeta «aportaciones»
y se apuntan en datos.py (APORTACIONES). Se enseñan tal como se entregaron.

Necesita:  pip install pymupdf pillow
"""
import io, json, os, re, shutil, subprocess, sys, tempfile, unicodedata
from html import escape as h
try:
    import pymupdf
except ImportError:                                  # versiones antiguas
    import fitz as pymupdf
from PIL import Image, ImageChops
from datos import BLOQUES, HILOS, SECCIONES, FIN_MOMENTOS, APORTACIONES, OBRA

AQUI = os.path.dirname(os.path.abspath(__file__))
ANCHO = 1240          # anchura en píxeles de cada página guardada
PROPIA = 'Elaboración propia'   # rótulo de los momentos que desarrolló la edición docente, como en el documento


def norm(s):
    s = unicodedata.normalize('NFKD', s)
    return re.sub(r'[^a-z0-9]', '', ''.join(c for c in s if not unicodedata.combining(c)).lower())


class Linea:
    __slots__ = ('p', 'x0', 'y0', 'y1', 'txt', 't', 'negrita')

    def __init__(self, p, x0, y0, y1, txt, negrita):
        txt = ' '.join(txt.replace('\u00a0', ' ').split())
        self.p, self.x0, self.y0, self.y1, self.txt, self.negrita = p, x0, y0, y1, txt, negrita
        self.t = norm(txt)


def leer(doc):
    """Líneas del cuerpo de todo el documento, en orden, y los márgenes útiles de cada página
    (por debajo del encabezado corrido y por encima del «Página N»)."""
    cuerpo, margen = [], []
    for p, page in enumerate(doc, 1):
        crudas = []
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0:
                continue
            for l in b['lines']:
                sp = [s for s in l['spans'] if s['text'].strip()]
                if sp:
                    crudas.append([l['bbox'][0], l['bbox'][1], l['bbox'][3], ''.join(s['text'] for s in l['spans']).strip(),
                                   all(s['flags'] & 16 for s in sp)])
        crudas.sort(key=lambda r: (r[1], r[0]))
        filas = []                                   # trozos de una misma línea visual, unidos
        for r in crudas:
            if filas and abs(filas[-1][1] - r[1]) < 3 and r[0] > filas[-1][0]:
                f = filas[-1]
                f[3] += ' ' + r[3]; f[2] = max(f[2], r[2])
            else:
                filas.append(list(r))
        arriba, abajo = 0.0, page.rect.height
        for x0, y0, y1, txt, neg in filas:
            t = norm(txt)
            if y0 < 45 and t.startswith('100momentosdehistoriadecanarias'):
                arriba = max(arriba, y1 + 5)
            elif y0 > page.rect.height - 60 and re.fullmatch(r'pagina\d+', t):
                abajo = min(abajo, y0 - 3)
            else:
                cuerpo.append(Linea(p, x0, y0, y1, txt, neg))
        margen.append((arriba, abajo))
    return cuerpo, margen


def localizar(L):
    """Encabezados «N. Título» de los cien momentos, en orden. Solo cuenta el que va seguido de
    «Autor/a del trabajo», «Autoría editorial» o «Momento pendiente»: así no se confunde con el índice ni los créditos."""
    es_marca = lambda l: l.t.startswith(('autoradeltrabajo', 'autoriaeditorial', 'momentopendiente'))
    cab, n, i = {}, 1, 0
    while i < len(L) and n <= 100:
        l = L[i]
        m = re.match(r'^(\d{1,3})\.\s+(\S.*)$', l.txt)
        if m and int(m.group(1)) == n and l.negrita:
            titulo, j, marca = [m.group(2)], i + 1, None
            while j < len(L) and j <= i + 5:
                if es_marca(L[j]):
                    marca = j; break
                if L[j].negrita and abs(L[j].x0 - l.x0) < 4:
                    titulo.append(L[j].txt); j += 1; continue
                break
            if marca is not None:
                cab[n] = dict(i=i, fin_titulo=marca - 1, titulo=' '.join(titulo))
                n += 1; i = marca; continue
        i += 1
    if len(cab) != 100:
        sys.exit(f'Solo se han localizado {len(cab)} de los 100 momentos (falta el {len(cab) + 1}).')
    return cab


def tinta(img, y0, y1):
    """Primera y última fila con algo dibujado entre dos alturas de la imagen."""
    y0, y1 = max(0, int(y0)), min(img.height, int(y1))
    if y1 - y0 < 2:
        return None
    zona = img.crop((0, y0, img.width, y1))
    caja = ImageChops.difference(zona, Image.new('RGB', zona.size, 'white')).convert('L').point(lambda v: 255 if v > 10 else 0).getbbox()
    return (y0 + caja[1], y0 + caja[3]) if caja else None


def perfil(img, y0, y1):
    """Cuánta tinta hay en cada fila (0-255) entre dos alturas."""
    zona = img.crop((0, int(y0), img.width, int(y1)))
    dif = ImageChops.difference(zona, Image.new('RGB', zona.size, 'white')).convert('L')
    return list(dif.resize((1, dif.height), Image.BOX).tobytes())


def en_pdf(ruta):
    """Un .docx se convierte primero a PDF con LibreOffice; un PDF se usa tal cual."""
    if not ruta.lower().endswith(('.docx', '.doc', '.odt')):
        return ruta
    exe = shutil.which('soffice') or shutil.which('libreoffice')
    if not exe:
        sys.exit('Para leer un documento de Word hace falta LibreOffice. Otra opción: guárdalo como PDF desde Word y pasa ese PDF.')
    tmp = tempfile.mkdtemp()
    subprocess.run([exe, '--headless', '--convert-to', 'pdf', '--outdir', tmp, ruta], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return os.path.join(tmp, os.path.splitext(os.path.basename(ruta))[0] + '.pdf')


def guardar(img, ruta):
    """WebP sin pérdida para las páginas de texto; con pérdida solo si la foto lo hace mucho más ligero."""
    a, b = io.BytesIO(), io.BytesIO()
    img.save(a, 'WEBP', lossless=True, quality=70, method=6)
    img.save(b, 'WEBP', quality=76, method=6)
    datos = a.getvalue() if len(a.getvalue()) <= len(b.getvalue()) * 1.15 else b.getvalue()
    open(ruta, 'wb').write(datos)
    return len(datos)


def main():
    if len([a for a in sys.argv[1:] if not a.startswith('--')]) < 1:
        sys.exit(__doc__)
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    pdf = args[0]
    salida = args[1] if len(args) > 1 else os.path.dirname(AQUI)
    os.makedirs(os.path.join(salida, 'paginas'), exist_ok=True)
    doc = pymupdf.open(en_pdf(pdf))
    L, margen = leer(doc)
    cab = localizar(L)

    # ── títulos, autoría y pendientes ──
    fin = next((i for i in range(cab[100]['i'], len(L)) if L[i].t.startswith(norm(FIN_MOMENTOS))), len(L))
    bloque = [i for i in range(len(L) - 1)                       # «II. Contactos…» + «10 de 10 aportaciones…» o «10 de 10 momentos…»
              if L[i].negrita and re.match(r'^[IVX]+\.\s', L[i].txt) and re.match(r'^\d+ de \d+ (aportaciones|momentos)', L[i + 1].txt)]
    M, corte = [], {}
    for n in range(1, 101):
        a = cab[n]['i']
        z = cab[n + 1]['i'] if n < 100 else fin
        z = min([b for b in bloque if a < b < z] + [z])          # antes del título del bloque siguiente
        autor = aviso = None
        propia = False                                           # «Autoría editorial: elaboración propia»: no es un trabajo del alumnado
        for i in range(a, z):
            if autor is None and L[i].t.startswith('autoradeltrabajo'):
                autor = (i, L[i].txt.split(':', 1)[1].strip() if ':' in L[i].txt else '')
            if autor is None and L[i].t.startswith('autoriaeditorial'):
                autor, propia = (i, ''), True
            if aviso is None and L[i].t.startswith('momentopendiente'):
                aviso = i
        nombre = None if autor is None else ('' if norm(autor[1]).startswith('nombrenoconsignado') else autor[1])
        M.append((cab[n]['titulo'], nombre, propia))
        corte[n] = dict(a=a, z=z, autor=autor[0] if autor else None, aviso=aviso)

    # ── páginas como imagen, a medida que hacen falta ──
    esc = ANCHO / doc[0].rect.width
    hojas = {}

    def hoja(p):
        if p not in hojas:
            pix = doc[p - 1].get_pixmap(matrix=pymupdf.Matrix(esc, esc), alpha=False)
            hojas[p] = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        return hojas[p]

    def tramos(pa, ya, pz, yz):
        """Recortes [página, arriba, abajo] en diezmilésimas de la altura, ajustados a la tinta."""
        out = []
        for p in range(pa, pz + 1):
            arriba = ya - 5 if p == pa else margen[p - 1][0]
            abajo = min(yz - 4, margen[p - 1][1]) if p == pz else margen[p - 1][1]
            img = hoja(p)
            t = tinta(img, arriba * esc, abajo * esc)
            if not t:
                continue
            y0 = max(arriba * esc, t[0] - 5 * esc); y1 = min(abajo * esc, t[1] + 7 * esc)
            if y1 - y0 > 6:
                out.append([p, round(y0 / img.height * 10000), round(y1 / img.height * 10000)])
        return out

    def hasta(i):                                    # posición donde termina un fragmento
        return (L[i].p, L[i].y0) if i < len(L) else (len(doc), margen[-1][1])

    F = {}
    for n in range(1, 101):
        if M[n - 1][1] is None:
            continue
        c = corte[n]; ini = L[c['a']]; pz, yz = hasta(c['z'])
        if c['aviso'] is not None and c['autor'] is not None and c['aviso'] < c['autor']:
            # Hay aportación, pero el PDF conserva encima un aviso de «pendiente» ya superado:
            # se enseña el encabezado y se retoma en la línea de autoría.
            tit = L[cab[n]['fin_titulo']]; img = hoja(ini.p)
            y = tit.y1 * esc
            filas = perfil(img, y, L[c['aviso']].y0 * esc)
            k = 0
            while k < len(filas) and filas[k] < 6: k += 1          # hasta el filete del título
            while k < len(filas) and filas[k] >= 6: k += 1         # el filete
            cabecera = tramos(ini.p, ini.y0, ini.p, (y + k + 2) / esc + 4)
            au = L[c['autor']]
            F[f'm{n}'] = cabecera + tramos(au.p, au.y0, pz, yz)
        else:
            F[f'm{n}'] = tramos(ini.p, ini.y0, pz, yz)
    for clave, _, empieza, acaba, _ in SECCIONES:
        a = next(i for i, l in enumerate(L) if l.t.startswith(norm(empieza)))
        z = next((i for i in range(a + 1, len(L)) if L[i].t.startswith(norm(acaba))), len(L)) if acaba else len(L)
        F[clave] = tramos(L[a].p, L[a].y0, *hasta(z))

    usadas = sorted({t[0] for f in F.values() for t in f})
    for viejo in os.listdir(os.path.join(salida, 'paginas')):
        os.remove(os.path.join(salida, 'paginas', viejo))
    peso = 0
    for p in usadas:
        peso += guardar(hoja(p), os.path.join(salida, 'paginas', f'{p:03d}.webp'))

    # ── aportaciones sueltas: el documento del estudiante, página a página ──
    ancho, alto = hoja(usadas[0]).size
    carpeta = next((c for c in (os.path.join(salida, 'aportaciones'), os.path.join(os.path.dirname(AQUI), 'aportaciones'),
                                os.path.join(AQUI, 'aportaciones')) if os.path.isdir(c)), None)
    for n, (archivo, autor) in sorted(APORTACIONES.items()):
        if M[n - 1][1] is not None:
            print(f'  aportación suelta {n}: el PDF de la edición ya la incluye; se usa la del PDF'); continue
        ruta = os.path.join(carpeta or '', archivo)
        if not os.path.isfile(ruta):
            sys.exit(f'Falta el archivo de la aportación {n}: aportaciones/{archivo}')
        suelta, tr = pymupdf.open(ruta), []
        for k, page in enumerate(suelta, 1):
            for w in page.get_text('words'):                 # el identificador de alumno no se publica
                if re.fullmatch(r'(?i)alu\d{6,12}', w[4].strip('.,;:()')):
                    page.add_redact_annot(pymupdf.Rect(w[:4]), fill=(1, 1, 1))
            page.apply_redactions()
            z = ancho / page.rect.width
            pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False)
            img = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
            if img.size != (ancho, alto):                    # mismo formato que las páginas de la edición
                lienzo = Image.new('RGB', (ancho, alto), 'white')
                lienzo.paste(img.crop((0, 0, min(ancho, img.width), min(alto, img.height))), (0, 0)); img = lienzo
            t = tinta(img, 0, alto)
            if not t:
                continue
            nombre = f'a{n}-{k}'
            peso += guardar(img, os.path.join(salida, 'paginas', nombre + '.webp'))
            tr.append([nombre, round(max(0, t[0] - 5 * z) / alto * 10000), round(min(alto, t[1] + 7 * z) / alto * 10000), k])
        F[f'm{n}'] = tr
        M[n - 1] = (M[n - 1][0], autor, False)

    # ── la página ──
    tpl = open(os.path.join(AQUI, 'plantilla.html'), encoding='utf-8').read()
    cinta, linea, matriz, autoria = [], [], [], []
    for b, (rom, nombre, corto, cuando) in enumerate(BLOQUES, 1):
        ns = range((b - 1) * 10 + 1, b * 10 + 1)
        cinta.append(f'        <button class="rb e{b}" type="button" aria-label="Ir al bloque {rom}: {h(nombre)}">'
                     f'<span class="r">{rom}</span><span class="s">{h(corto)}</span></button>')
        filas = []
        for n in ns:
            t, a, propia = M[n - 1]
            cls = ('up' if n % 2 else 'dn') + (' pend' if a is None else '')
            dentro = (f'<span class="num">{n}</span><span class="tt">{h(t)}</span>'
                      + (f'<span class="by">{h(a)}</span>' if a else f'<span class="by ed">{PROPIA}</span>' if propia else ''))
            ficha = f'<span class="card">{dentro}</span>' if a is None else f'<a class="card" href="#m{n}">{dentro}</a>'
            filas.append(f'          <li class="m {cls}" data-n="{n}">{ficha}<span class="dot"></span></li>')
        linea.append(f'        <section class="era e{b}" aria-labelledby="b{b}">\n'
                     f'          <header class="era-head"><span class="r" aria-hidden="true">{rom}</span><h2 id="b{b}">{h(nombre)}</h2>'
                     + (f'<span class="w">{h(cuando)}</span>' if cuando else '') + '</header>\n'
                     f'          <ol class="ms" start="{ns[0]}">\n' + '\n'.join(filas) + '\n          </ol>\n        </section>')
        celdas = ''.join(
            f'<span class="cell pend" data-n="{n}" aria-label="{n}. {h(M[n-1][0])}">{n}</span>' if M[n - 1][1] is None else
            f'<a class="cell" data-n="{n}" href="#m{n}" aria-label="{n}. {h(M[n-1][0])}{". " + h(M[n-1][1] or PROPIA) if M[n-1][1] or M[n-1][2] else ""}">{n}</a>'
            for n in ns)
        matriz.append(f'        <div class="mx-row e{b}"><span class="lab"><b>{rom}</b><span>{h(corto)}</span></span>{celdas}</div>')
        for n in ns:
            t, a, _ = M[n - 1]
            if a:
                autoria.append(f'        <li class="e{b}"><a href="#m{n}"><span class="n">{n}</span>'
                               f'<span class="a">{h(a)}</span><span class="t">{h(t)}</span></a></li>')
    datos = dict(m=[[t, a, 1] if e else [t, a] for t, a, e in M], eras=[list(b) for b in BLOQUES], hilos=[[k, nom, lst] for k, nom, lst in HILOS],
                 secs=[[s[0], s[1]] for s in SECCIONES], f=F, r=round(hoja(usadas[0]).height / hoja(usadas[0]).width, 5),
                 o=dict(t=OBRA['titulo'], c=OBRA['coordinacion_cita'], y=OBRA['anio'], i=OBRA['institucion'], u=OBRA['url']))
    firmas = list(dict.fromkeys(a for _, a, _ in M if a))           # nombres, sin repetir y en orden
    ficha = {                                                     # metadatos académicos legibles por buscadores
        '@context': 'https://schema.org', '@type': 'CreativeWork', 'name': OBRA['titulo'], 'inLanguage': 'es',
        'datePublished': OBRA['anio'], 'abstract': OBRA['resumen'], 'keywords': OBRA['palabras_clave'],
        'about': {'@type': 'Thing', 'name': 'Historia de Canarias'},
        'learningResourceType': 'Obra colectiva de alumnado universitario',
        'editor': {'@type': 'Person', 'name': OBRA['coordinacion']},
        'author': [{'@type': 'Person', 'name': a} for a in firmas],
        'sourceOrganization': {'@type': 'CollegeOrUniversity', 'name': OBRA['institucion'], 'url': OBRA['institucion_url']},
    }
    if OBRA['url']:
        ficha['url'] = OBRA['url']
    campos = {'%%TITULO%%': OBRA['titulo'], '%%INSTITUCION%%': OBRA['institucion'], '%%INSTITUCION_URL%%': OBRA['institucion_url'],
              '%%TITULACION%%': OBRA['titulacion'], '%%ASIGNATURA%%': OBRA['asignatura'], '%%CURSO%%': OBRA['curso'], '%%ANIO%%': OBRA['anio'],
              '%%COORDINACION%%': OBRA['coordinacion'], '%%COORD_CITA%%': OBRA['coordinacion_cita'], '%%RESUMEN%%': OBRA['resumen'],
              '%%PALABRAS%%': '; '.join(OBRA['palabras_clave']) + '.'}
    # cuántos momentos son del alumnado y cuántos de elaboración propia: de ahí salen cuatro frases de la página
    propias = [n for n in range(1, 101) if M[n - 1][2]]
    alum = sum(1 for _, a, e in M if a is not None and not e)
    quien = f'el alumnado de {OBRA["asignatura"]}, en la {OBRA["institucion"]},'
    if propias:
        campos['%%ENTRADA%%'] = (f'Cien procesos y acontecimientos: {alum} investigados uno a uno por {quien} y {len(propias)} desarrollados '
                                 'por la edición docente. Abre cualquiera: se muestra tal como quedó en la edición.')
        campos['%%AUTORIA_FICHA%%'] = (f'{alum} trabajos individuales del alumnado y {len(propias)} momentos de elaboración propia de la edición docente')
    else:
        campos['%%ENTRADA%%'] = (f'Cien procesos y acontecimientos que {quien} investigó uno a uno. '
                                 'Recorre la línea y abre cualquiera: se muestra tal como quedó en la edición docente.')
        campos['%%AUTORIA_FICHA%%'] = f'{alum} trabajos individuales del alumnado'
    for k, v in campos.items():
        tpl = tpl.replace(k, h(v))
    tpl = tpl.replace('%%PROPIAS%%', '' if not propias else
                      '      <p class="au-ed">' + PROPIA + ' de la edición docente, sin autoría del alumnado: '
                      + ', '.join(f'<a href="#m{n}" title="{h(M[n - 1][0])}">{n}</a>' for n in propias) + '.</p>')
    tpl = tpl.replace('%%JSONLD%%', json.dumps(ficha, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/'))
    out = (tpl.replace('%%CINTA%%', '\n'.join(cinta))
              .replace('%%HILOS%%', '\n'.join(f'        <button class="chip" type="button" aria-pressed="false">{h(n)}</button>' for _, n, _ in HILOS))
              .replace('%%LINEA%%', '\n'.join(linea)).replace('%%MATRIZ%%', '\n'.join(matriz)).replace('%%AUTORIA%%', '\n'.join(autoria))
              .replace('%%DATOS%%', json.dumps(datos, ensure_ascii=False, separators=(',', ':'))))
    assert '%%' not in out, 'queda un marcador sin sustituir'
    cabeza, cuerpo = out.split('<!--CUERPO-->')
    completo = ('<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
                '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
                '<meta name="color-scheme" content="light dark">\n'
                f'<meta name="description" content="Línea temporal con cien momentos de Historia de Canarias: obra colectiva del alumnado de '
                f'{h(OBRA["asignatura"])} ({h(OBRA["institucion"])}).">\n'
                f'<meta name="author" content="Alumnado de {h(OBRA["asignatura"])}, {h(OBRA["institucion"])}. Coordinación: {h(OBRA["coordinacion"])}">\n'
                + cabeza.strip() +
                '\n<style>:root{padding-block:env(safe-area-inset-top,0px) env(safe-area-inset-bottom,0px)}</style>\n'
                '</head>\n<body>' + cuerpo.rstrip() + '\n</body>\n</html>\n')
    open(os.path.join(salida, 'index.html'), 'w', encoding='utf-8').write(completo)
    if '--previa' in sys.argv:                       # extras para revisar el resultado; no forman parte de la web
        open(os.path.join(salida, 'vista-previa.html'), 'w', encoding='utf-8').write(out)
        json.dump(dict(M=M, F=F), open(os.path.join(salida, 'extraido.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    con = sum(1 for _, a, _ in M if a is not None)
    sueltas = sum(len(F[f'm{n}']) for n in APORTACIONES if f'm{n}' in F and isinstance(F[f'm{n}'][0][0], str))
    print(f'{alum} momentos del alumnado, {len(propias)} de elaboración propia, {100 - con} pendientes · {len(usadas)} páginas de la edición + {sueltas} de aportaciones sueltas ({peso / 1e6:.1f} MB) · index.html {len(completo.encode()) // 1024} KB')


if __name__ == '__main__':
    main()
