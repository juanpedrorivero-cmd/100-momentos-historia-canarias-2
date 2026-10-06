# 100 momentos de Historia de Canarias · web

Línea temporal con los cien momentos. Al pulsar uno se abre **su fragmento del documento original**,
tal como está maquetado, con sus imágenes: la web no reescribe ni recompone los trabajos.

Está generada desde la edición completa: 90 momentos del alumnado y 10 de elaboración propia de la edición docente
(21, 27, 49, 53, 60, 73, 79, 90, 91 y 96). Estos diez llevan el rótulo «Elaboración propia» en la línea, en la matriz,
al abrirlos y en su cita, y no figuran en el índice de autoría, para que no se confundan con los trabajos del alumnado.

## Qué hay en esta carpeta

| Archivo | Para qué |
|---|---|
| `index.html` | La web. |
| `paginas/` | Cada página del documento como imagen. La web muestra recortes de estas imágenes. |
| `fuentes/` | El generador: lee el documento y produce `index.html` y `paginas/`. |
| `.github/workflows/generar.yml` | Hace que GitHub ejecute el generador solo cuando se sube una edición nueva. |

## Publicar en GitHub Pages

1. Crea un repositorio y sube todo el contenido de esta carpeta a la raíz, **más el documento de la edición** (el Word o un PDF).
2. En el repositorio: **Settings → Pages → Deploy from a branch → `main` / `(root)`**.
3. La web queda en `https://<usuario>.github.io/<repositorio>/`.

Subiendo por el navegador, GitHub admite 100 archivos por tanda: `paginas/` tiene más, así que va en dos tandas.

## Quién puede cambiar el contenido

Solo quien tenga permiso de escritura en el repositorio. Los visitantes solo leen.

## Cuando llegue una edición nueva

Sustituye el documento de la raíz por el nuevo, en Word (`.docx`) o en PDF, y deja uno solo. GitHub regenera la web
en unos minutos: títulos, autoría, momentos que dejan de estar pendientes, páginas e imágenes salen del propio documento.

Para hacerlo a mano en un ordenador:

    pip install pymupdf pillow
    python fuentes/generar.py edicion.docx        (o edicion.pdf)

Con un `.docx` hace falta tener LibreOffice instalado, que es quien lo pasa a PDF; reproduce la maquetación de Word
línea por línea. Si prefieres el PDF exacto de Word, guárdalo desde Word como PDF y usa ese.

El generador reconoce cada momento por su encabezado «N. Título» seguido de «Autor/a del trabajo»,
de «Autoría editorial: elaboración propia» o de «Momento pendiente de incorporar». Si una edición futura cambia
esa forma de encabezar, se detiene y dice qué momento no encuentra.

## Añadir un trabajo que llega suelto

Con la edición completa ya no hace falta. Queda el mecanismo por si una edición futura vuelve a dejar algún momento
pendiente y un estudiante entrega el suyo después de cerrarla:

1. Guarda su documento como PDF (en Word: *Guardar como → PDF*) con el número del momento, en una carpeta `aportaciones`: `aportaciones/83.pdf`.
2. Apúntalo en `fuentes/datos.py`, en la lista `APORTACIONES`: `83: ("83.pdf", "Nombre Apellidos"),`
3. Sube los dos cambios. GitHub regenera la web, o ejecuta el generador a mano.

El momento deja de estar pendiente y se abre mostrando el trabajo tal como se entregó.
El generador borra de esas páginas los identificadores de alumno (`aluXXXXXXXXXX`), pero el PDF que subas al
repositorio es público: súbelo ya sin ese dato. No subas el `.docx` original.

Cuando una edición nueva del PDF incluya ese momento, manda el PDF y la aportación suelta deja de usarse.

## Qué decide la web y no el documento

Está todo en `fuentes/datos.py` y se puede corregir:

- **Hilos de larga duración**: agrupan momentos por las claves del bloque X, a partir de los títulos.
- **Nombres cortos y etiquetas temporales** de los bloques («orígenes», «1900–1936», «desde 1975»).
- **Ficha académica** (bloque `OBRA`): institución, titulación, asignatura, curso, coordinación, año de las citas,
  resumen y palabras clave. De ahí salen la sección «Sobre esta obra», la cita sugerida de la obra, la cita de cada
  momento y los metadatos de la página. El resumen y las palabras clave los redacté yo a partir de la introducción
  del documento: conviene que los revise el coordinador.

Además:

- Si una edición dejara momentos sin desarrollar, aparecerían en hueco, sin rótulo y sin enlace. Hoy no hay ninguno.
- El momento 8 no lleva nombre porque el documento indica que el archivo original no lo consignaba.
- No se enlaza la «Presentación editorial» del documento, porque es la auditoría interna de entregas.
- El mapa de la portada usa los contornos de Natural Earth (dominio público).
- Las citas llevan el nombre de cada estudiante tal como figura en el documento, sin invertirlo a «Apellidos, N.»:
  separar nombre y apellidos a máquina falla con nombres compuestos.
- Los momentos de elaboración propia se citan por el título, seguidos de «Elaboración propia de la edición docente»,
  sin atribuirlos a una persona: el documento no los firma con nombre.
- La dirección de la web se añade sola al final de las citas cuando la página se sirve desde `github.io`. Con un
  dominio propio, escríbela en `url` dentro de `OBRA`.
- La web nombra y enlaza la Universidad de La Laguna, pero no usa su logotipo ni su identidad visual: eso requiere
  autorización de la universidad y daría a entender que es una página oficial.

## Antes de hacerla pública

El propio documento advierte que, antes de una publicación digital abierta, hay que verificar procedencia,
licencia y derechos de reproducción de cada imagen. GitHub Pages es público.

## Dependencias externas

Solo las tipografías (Ibarra Real Nova y Archivo, desde Google Fonts). Todo lo demás está en esta carpeta.
