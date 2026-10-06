# -*- coding: utf-8 -*-
"""Lo único que no sale del PDF: nombres cortos de los bloques, hilos y secciones.
Títulos, autoría (del alumnado o elaboración propia de la edición), momentos pendientes y páginas
los lee generar.py del propio documento."""

BLOQUES = [
    # (romano, nombre completo, nombre corto, etiqueta temporal; vacía si el nombre ya la dice)
    ("I", "Formación y poblamiento antiguo", "Poblamiento antiguo", "orígenes"),
    ("II", "Contactos europeos y conquista", "Conquista", "siglos XIV–XV"),
    ("III", "Configuración de la sociedad atlántica", "Sociedad atlántica", "siglos XVI–XVII"),
    ("IV", "Siglo XVIII: reformas y cambios estructurales", "Reformas", ""),
    ("V", "Siglo XIX: liberalismo y economía de exportación", "Liberalismo", ""),
    ("VI", "Primer tercio del siglo XX", "Primer tercio", "1900–1936"),
    ("VII", "Guerra civil y franquismo", "Guerra y franquismo", "1936–1975"),
    ("VIII", "Democracia y autonomía", "Democracia", "desde 1975"),
    ("IX", "Siglo XXI", "Siglo XXI", ""),
    ("X", "Claves estructurales de larga duración", "Claves", ""),
]

# Hilos de larga duración: cada clave del bloque X (91-100) enlazada con los momentos
# de la línea que tratan el mismo asunto. Agrupación orientativa hecha a partir de los
# títulos; es una ayuda de navegación, no una clasificación del documento.
HILOS = [
    (91, "Insularidad", [1, 2, 39, 90, 91]),
    (92, "Economías de exportación", [23, 27, 35, 37, 43, 46, 52, 66, 76, 82, 92]),
    (93, "Movilidad migratoria", [3, 29, 47, 65, 77, 93]),
    (94, "Puertos", [11, 26, 34, 45, 51, 94]),
    (95, "Gestión del agua", [19, 58, 95]),
    (96, "Presencia de la Iglesia", [14, 21, 22, 25, 28, 32, 44, 53, 63, 67, 74, 79, 86, 96]),
    (97, "Pluralidad cultural", [4, 13, 29, 77, 86, 97]),
    (98, "Patrimonio", [9, 10, 25, 36, 57, 75, 98]),
    (99, "Equilibrios interinsulares", [18, 39, 41, 72, 78, 99]),
    (100, "Identidad canaria", [4, 6, 9, 33, 60, 97, 100]),
]

# Partes del documento que no son momentos: (clave, etiqueta, texto con el que empieza,
# texto con el que termina o None, página orientativa)
SECCIONES = [
    ("introduccion", "Introducción", "Introducción: cien momentos", "I. Formación y poblamiento antiguo", 7),
    ("conclusion", "Conclusión general del profesor", "Conclusión general del profesor", None, 148),
]

FIN_MOMENTOS = "Apéndice editorial"   # lo que sigue al momento 100

# Aportaciones recibidas después de cerrar el PDF de la edición docente. Se muestran tal como
# las entregó cada estudiante hasta que una edición nueva del PDF las incluya; entonces manda el PDF.
#   número de momento: (archivo PDF dentro de la carpeta «aportaciones», autor/a)
APORTACIONES = {
    # 83: ("83.pdf", "Nombre Apellidos"),
}

# Ficha académica de la obra: sale en «Sobre esta obra», en las citas y en los metadatos de la página.
OBRA = dict(
    titulo="100 momentos de Historia de Canarias",
    institucion="Universidad de La Laguna",
    institucion_url="https://www.ull.es",
    titulacion="Grado en Maestro/a en Educación Primaria",
    asignatura="Didáctica de las Ciencias Sociales I",
    curso="2026/2027",
    anio="2026",                               # año que figura en las citas
    coordinacion="Juan Pedro Rivero González",
    coordinacion_cita="Rivero González, J. P.",  # tal como debe aparecer en una cita
    url="",                                    # dirección pública de la web; vacía = se toma sola en GitHub Pages
    resumen=("Esta obra colectiva reúne cien momentos de la Historia de Canarias: noventa ordenados cronológicamente, "
             "desde la formación volcánica del archipiélago hasta el siglo XXI, y diez claves de larga duración que los "
             "atraviesan. El alumnado investigó individualmente la mayor parte: cada estudiante localizó y contrastó fuentes, "
             "situó su momento en contexto, explicó sus consecuencias y su interpretación historiográfica y comentó una imagen "
             "o un documento histórico. Los momentos que quedaron sin aportación los desarrolló la edición docente y figuran "
             "como elaboración propia. El conjunto convierte esas investigaciones en una secuencia compartida, pensada para "
             "aprender y enseñar historia desde la formación inicial del profesorado."),
    palabras_clave=["Historia de Canarias", "Didáctica de las Ciencias Sociales", "formación inicial del profesorado",
                    "fuentes históricas", "obra colectiva"],
)
