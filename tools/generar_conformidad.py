#!/usr/bin/env python3
"""Genera los casos de conformidad de validación, aritmética, vigencia y respuestas.

Uso:  python3 tools/generar_conformidad.py              escribe los casos en conformidad/
      python3 tools/generar_conformidad.py --verificar  no escribe: falla si los casos no están al día

Entradas: los documentos base de conformidad/bases/ (XML sin firmar que se generaron una sola vez con un SDK y se
validaron contra el XSD oficial), las reglas de reglas/, los campos de campos/, los códigos de respuestas/ y la
lista conformidad/cobertura.json. Salida: un JSON por caso y su XML al lado (ver conformidad/README.md).

Los resultados esperados salen de las reglas, con una implementación de referencia mínima de las fórmulas
aritméticas y de la gramática de condiciones (FORMATO.md). No sale de ningún SDK. Sin dependencias: biblioteca
estándar de Python 3.
"""
import datetime
import glob
import json
import os
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from fractions import Fraction

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(RAIZ, "conformidad")
NS = "http://ekuatia.set.gov.py/sifen/xsd"
ET.register_namespace("", NS)
DECLARACION = '<?xml version="1.0" encoding="UTF-8"?>'
MEDIO = Fraction(1, 2)
TIPOS_GENERADOS = ("validacion", "aritmetica", "vigencia", "respuestas")

# Raíz del árbol que evalúa cada perfil: el documento electrónico y los eventos.
RAICES = {"rDE": "AA001", "rGesEve": "GDE001"}
# Campo de fecha que elige las reglas vigentes: emisión del DE (D002) o firma del evento (GDE004).
CAMPO_FECHA = {"rDE": "D002", "rGesEve": "GDE004"}

# Documentos base, en el orden en que se buscan para un caso de falla.
BASES = [
    ("factura", "Factura electrónica en guaraníes: ítems al 10 %, al 5 %, exento, exonerado y gravado parcial, "
                "con descuento particular en un ítem"),
    ("autofactura", "Autofactura electrónica (C002 = 4)"),
    ("factura-usd-cambio-global", "Factura electrónica en dólares con tipo de cambio global (D017 = 1)"),
    ("factura-usd-cambio-por-item", "Factura electrónica en dólares con tipo de cambio por ítem (D017 = 2)"),
    ("factura-energia", "Factura electrónica con el grupo del sector energía eléctrica (E791)"),
    ("nota-credito", "Nota de crédito electrónica (C002 = 5) asociada a la factura base"),
    ("nota-debito", "Nota de débito electrónica (C002 = 6) asociada a la factura base"),
    ("nota-remision", "Nota de remisión electrónica (C002 = 7)"),
    ("evento-cancelacion", "Evento de cancelación"),
    ("evento-inutilizacion", "Evento de inutilización de números"),
    ("evento-nominacion", "Evento de nominación del receptor"),
    ("evento-actualizacion-transporte", "Evento de actualización de datos del transporte"),
    ("evento-notificacion-recepcion", "Evento de notificación de recepción de un DE"),
    ("evento-conformidad", "Evento de conformidad con un DE"),
    ("evento-disconformidad", "Evento de disconformidad con un DE"),
    ("evento-desconocimiento", "Evento de desconocimiento de un DE"),
]


class NoCalculable(Exception):
    """Falta un operando obligatorio o no es un número: la regla no se puede verificar en este documento."""


# --- especificación ---------------------------------------------------------------------------------------------

def cargar_json(ruta):
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def cargar_spec():
    campos = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "campos", "*.json"))):
        for c in cargar_json(ruta)["campos"]:
            campos[c["id"]] = c
    reglas = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "reglas", "*.json"))):
        for r in cargar_json(ruta)["reglas"]:
            reglas[r["id"]] = r
    respuestas = {}
    for ruta in sorted(glob.glob(os.path.join(RAIZ, "respuestas", "*.json"))):
        for r in cargar_json(ruta)["respuestas"]:
            respuestas[(r["codigo"], r["servicio"])] = r
    return campos, reglas, respuestas


CAMPOS, REGLAS, RESPUESTAS = cargar_spec()
HIJOS = {}
for _c in CAMPOS.values():
    _clave = (_c.get("padre"), _c["xml"].split(":")[-1])
    _otro = HIJOS.get(_clave)
    if _otro is None or (_c.get("estado", "vigente") == "vigente" and _otro.get("estado", "vigente") != "vigente"):
        HIJOS[_clave] = _c


def repetible(fid):
    maximo = CAMPOS[fid]["ocurrencia"].split("-")[1]
    return maximo == "N" or int(maximo) > 1


def cadena(fid):
    """El campo y sus ancestros, del campo a la raíz."""
    out = []
    while fid is not None and fid not in out:
        out.append(fid)
        fid = CAMPOS[fid].get("padre") if fid in CAMPOS else None
    return out


def vigente(entrada, ambiente, fecha):
    """Si una regla rige en una fecha y un ambiente (FORMATO.md, Vigencia).

    `hasta` excluye su fecha. Un `hasta` con fecha null significa que una fuente posterior reemplazó la entrada
    sin publicar cuándo: para una fecha actual se toma como reemplazada.
    """
    v = entrada.get("vigencia") or {}
    desde = (v.get("desde") or {}).get(ambiente)
    if desde is not None and fecha < desde:
        return False
    hasta = v.get("hasta") or {}
    if ambiente in hasta:
        return hasta[ambiente] is not None and fecha < hasta[ambiente]
    return True


# --- documento ---------------------------------------------------------------------------------------------------

class Nodo:
    """Un elemento del XML con el id de su campo."""

    def __init__(self, elem, fid, padre):
        self.elem, self.fid, self.padre = elem, fid, padre
        self.hijos = []

    @property
    def nombre(self):
        return self.elem.tag.split("}")[-1]

    @property
    def texto(self):
        return self.elem.text

    def ancestros(self):
        n = self
        while n is not None:
            yield n
            n = n.padre

    def descendientes(self):
        for h in self.hijos:
            yield h
            yield from h.descendientes()

    def ruta(self):
        partes = []
        for n in self.ancestros():
            p = n.padre
            seg = n.nombre
            if p is not None:
                iguales = [h for h in p.hijos if h.nombre == n.nombre]
                if len(iguales) > 1:
                    seg += f"[{iguales.index(n) + 1}]"
            partes.append(seg)
        return "/".join(reversed(partes))


class Documento:
    def __init__(self, raiz_elem):
        self.raiz_elem = raiz_elem
        nombre = raiz_elem.tag.split("}")[-1]
        if raiz_elem.tag != f"{{{NS}}}{nombre}" or nombre not in RAICES:
            raise ValueError(f"raíz inesperada {raiz_elem.tag}")
        self.tipo = nombre
        self.raiz = self._nodo(raiz_elem, RAICES[nombre], None)

    def _nodo(self, elem, fid, padre):
        n = Nodo(elem, fid, padre)
        for e in elem:
            nombre = e.tag.split("}")[-1]
            c = HIJOS.get((fid, nombre)) if fid else None
            n.hijos.append(self._nodo(e, c["id"] if c else None, n))
        return n

    def todos(self, fid):
        return [n for n in self.raiz.descendientes() if n.fid == fid] + ([self.raiz] if self.raiz.fid == fid else [])

    def fecha(self):
        n = self.todos(CAMPO_FECHA[self.tipo])
        return n[0].texto[:10] if n else None


def leer(ruta):
    return Documento(ET.parse(ruta).getroot())


def escribir_xml(doc):
    return DECLARACION + ET.tostring(doc.raiz_elem, encoding="unicode")


def contexto(doc, nodo, fid):
    """Ocurrencias de un campo vistas desde un nodo (FORMATO.md, Campos que se repiten)."""
    destino = cadena(fid)
    for a in nodo.ancestros():
        if a.fid is not None and a.fid in destino and repetible(a.fid):
            return [n for n in a.descendientes() if n.fid == fid] + ([a] if a.fid == fid else [])
    return doc.todos(fid)


def decimal(texto):
    try:
        return Fraction(Decimal(texto.strip()))
    except (InvalidOperation, AttributeError, ValueError):
        return None


def mismo(a, b):
    if a == b:
        return True
    da, db = decimal(a), decimal(b)
    return da is not None and db is not None and da == db


def cumple(doc, nodo, c):
    """Evalúa una condición de la gramática de FORMATO.md desde un nodo."""
    if "todas" in c:
        return all(cumple(doc, nodo, s) for s in c["todas"])
    if "alguna" in c:
        return any(cumple(doc, nodo, s) for s in c["alguna"])
    if "no" in c:
        return not cumple(doc, nodo, c["no"])
    ocurrencias = contexto(doc, nodo, c["campo"])
    op = c["op"]
    if op == "presente":
        return bool(ocurrencias)
    if op == "ausente":
        return not ocurrencias
    if not ocurrencias:
        return op == "no_en"

    def una(v):
        if op == "igual":
            return mismo(v, c["valor"])
        if op == "distinto":
            return not mismo(v, c["valor"])
        if op == "en":
            return any(mismo(v, x) for x in c["valores"])
        if op == "no_en":
            return not any(mismo(v, x) for x in c["valores"])
        a, b = decimal(v), decimal(c["valor"])
        if a is None or b is None:
            return False
        return {"mayor": a > b, "mayor_igual": a >= b, "menor": a < b, "menor_igual": a <= b}[op]

    valores = [o.texto for o in ocurrencias]
    if c.get("cuantificador") == "todos":
        return all(una(v) for v in valores)
    return any(una(v) for v in valores)


# --- implementación de referencia de las reglas aritméticas ------------------------------------------------------
#
# Cada función recibe el documento y la ocurrencia del campo de la regla, y devuelve el valor exacto de la fórmula
# (Fraction) o, en las reglas que comparan en lugar de calcular, un booleano. Los operandos se leen de la misma
# repetición (el mismo ítem) cuando comparten grupo con el campo; las sumatorias recorren los ítems y usan los
# valores informados. Un importe opcional que no figura (descuentos, anticipos, subtotales, redondeo, comisión,
# IVA del redondeo y de la comisión) cuenta como 0; si falta un operando obligatorio la regla no se puede verificar.

def req(doc, n, fid):
    oc = contexto(doc, n, fid)
    v = decimal(oc[0].texto) if oc else None
    if v is None:
        raise NoCalculable(fid)
    return v


def opc(doc, n, fid):
    oc = contexto(doc, n, fid)
    if not oc:
        return Fraction(0)
    v = decimal(oc[0].texto)
    if v is None:
        raise NoCalculable(fid)
    return v


def items(doc):
    return doc.todos("E700")


def en_item(doc, item, fid):
    oc = [n for n in item.descendientes() if n.fid == fid]
    return oc[0].texto if oc else None


def num_item(doc, item, fid, opcional=False):
    t = en_item(doc, item, fid)
    if t is None and opcional:
        return Fraction(0)
    v = decimal(t) if t is not None else None
    if v is None:
        raise NoCalculable(fid)
    return v


def suma(doc, termino):
    return sum((termino(i) for i in items(doc)), Fraction(0))


def afectacion(doc, item):
    return en_item(doc, item, "E731")


def tasa_es(doc, item, tasa):
    t = en_item(doc, item, "E734")
    return t is not None and decimal(t) == tasa


def base_nt13(doc, n, exenta):
    total, prop, tasa = req(doc, n, "EA008"), req(doc, n, "E733"), req(doc, n, "E734")
    num = 100 * total * ((100 - prop) if exenta else prop)
    return num / (10000 + tasa * prop)


def gravado_a(doc, tasa, nt13):
    def termino(i):
        if not tasa_es(doc, i, tasa):
            return Fraction(0)
        if not nt13:
            return num_item(doc, i, "EA008")
        af = afectacion(doc, i)
        if af == "1":
            return num_item(doc, i, "EA008")
        if af == "4":
            return num_item(doc, i, "E735") + num_item(doc, i, "E736")
        return Fraction(0)
    return suma(doc, termino)


def de_items_a(doc, fid, tasa):
    return suma(doc, lambda i: num_item(doc, i, fid) if tasa_es(doc, i, tasa) else Fraction(0))


def producto_items(doc, fid):
    return suma(doc, lambda i: num_item(doc, i, fid, opcional=True) * num_item(doc, i, "E711"))


def fecha_hora(doc, n, fid):
    oc = contexto(doc, n, fid)
    if not oc:
        raise NoCalculable(fid)
    try:
        return datetime.datetime.fromisoformat(oc[0].texto.strip())
    except ValueError:
        raise NoCalculable(fid)


def entero(doc, n, fid):
    oc = contexto(doc, n, fid)
    if not oc or not oc[0].texto.strip().isdigit():
        raise NoCalculable(fid)
    return int(oc[0].texto)


REFERENCIA = {
    "R-E727-A1": lambda d, n: req(d, n, "E721") * req(d, n, "E711"),
    "R-EA003-A1": lambda d, n: req(d, n, "EA002") * 100 / req(d, n, "E721"),
    "R-EA004-A2": lambda d, n: req(d, n, "F010") * req(d, n, "E721") / 100,
    "R-EA008-A1": lambda d, n: (req(d, n, "E721") - opc(d, n, "EA002") - opc(d, n, "EA004") - opc(d, n, "EA006")
                                - opc(d, n, "EA007")) * req(d, n, "E711"),
    "R-EA008-A2": lambda d, n: req(d, n, "E721") * req(d, n, "E711"),
    "R-EA009-A1": lambda d, n: req(d, n, "EA008") * req(d, n, "E725"),
    "R-E735-A1": lambda d, n: Fraction(0),
    "R-E735-A2": lambda d, n: req(d, n, "EA008") * (req(d, n, "E733") / 100) / Fraction("1.05"),
    "R-E735-A3": lambda d, n: req(d, n, "EA008") * (req(d, n, "E733") / 100) / Fraction("1.1"),
    "R-E735-A4": lambda d, n: base_nt13(d, n, False),
    "R-E735-A5": lambda d, n: base_nt13(d, n, False),
    "R-E736-A1": lambda d, n: Fraction(0),
    "R-E736-A2": lambda d, n: req(d, n, "E735") * (req(d, n, "E734") / 100),
    "R-E737-A1": lambda d, n: base_nt13(d, n, True),
    "R-E737-A2": lambda d, n: Fraction(0),
    "R-E797-A1": lambda d, n: req(d, n, "E796") - req(d, n, "E795"),
    "R-F002-A1": lambda d, n: suma(d, lambda i: num_item(d, i, "EA008") if afectacion(d, i) == "3" else Fraction(0)),
    "R-F002-A2": lambda d, n: suma(d, lambda i: num_item(d, i, "EA008") if afectacion(d, i) == "3"
                                   else num_item(d, i, "E737") if afectacion(d, i) == "4" else Fraction(0)),
    "R-F003-A1": lambda d, n: suma(d, lambda i: num_item(d, i, "EA008") if afectacion(d, i) == "2" else Fraction(0)),
    "R-F004-A1": lambda d, n: gravado_a(d, 5, False),
    "R-F004-A2": lambda d, n: gravado_a(d, 5, True),
    "R-F005-A1": lambda d, n: gravado_a(d, 10, False),
    "R-F005-A2": lambda d, n: gravado_a(d, 10, True),
    "R-F008-A1": lambda d, n: opc(d, n, "F002") + opc(d, n, "F003") + opc(d, n, "F004") + opc(d, n, "F005"),
    "R-F008-A3": lambda d, n: suma(d, lambda i: num_item(d, i, "EA008")),
    "R-F009-A2": lambda d, n: producto_items(d, "EA002"),
    "R-F033-A2": lambda d, n: producto_items(d, "EA004"),
    "R-F034-A2": lambda d, n: producto_items(d, "EA006"),
    "R-F035-A2": lambda d, n: producto_items(d, "EA007"),
    "R-F011-A2": lambda d, n: opc(d, n, "F009") + opc(d, n, "F033"),
    "R-F012-A2": lambda d, n: opc(d, n, "F034") + opc(d, n, "F035"),
    "R-F014-A1": lambda d, n: req(d, n, "F008") - opc(d, n, "F013") + opc(d, n, "F025"),
    "R-F014-A3": lambda d, n: req(d, n, "F008") - opc(d, n, "F013") + opc(d, n, "F025"),
    "R-F015-A1": lambda d, n: de_items_a(d, "E736", 5),
    "R-F016-A1": lambda d, n: de_items_a(d, "E736", 10),
    "R-F017-A1": lambda d, n: (opc(d, n, "F015") + opc(d, n, "F016") - opc(d, n, "F036") - opc(d, n, "F037")
                               + opc(d, n, "F026")),
    "R-F018-A1": lambda d, n: de_items_a(d, "E735", 5),
    "R-F019-A1": lambda d, n: de_items_a(d, "E735", 10),
    "R-F020-A1": lambda d, n: opc(d, n, "F018") + opc(d, n, "F019"),
    "R-F023-A1": lambda d, n: req(d, n, "F014") * req(d, n, "D018"),
    "R-F023-A2": lambda d, n: suma(d, lambda i: num_item(d, i, "EA009")),
    # Reglas que comparan en lugar de calcular: devuelven si se cumplen.
    "R-GEI006-A1": lambda d, n: entero(d, n, "GEI006") - entero(d, n, "GEI005") <= 1000,
    "R-GEI006-A2": lambda d, n: entero(d, n, "GEI006") > entero(d, n, "GEI005"),
    "R-GEI006-A3": lambda d, n: entero(d, n, "GEI006") - entero(d, n, "GEI005") + 1 <= 1000,
    "R-GEN004-A1": lambda d, n: fecha_hora(d, n, "GEN004") >= fecha_hora(d, n, "GEN003"),
    "R-GED004-A1": lambda d, n: fecha_hora(d, n, "GED004") >= fecha_hora(d, n, "GED003"),
}


def cobertura():
    return cargar_json(os.path.join(CONF, "cobertura.json"))


def sin_caso():
    return {e["regla"] for e in cobertura()["aritmetica_sin_caso"]}


def tolerancia(regla):
    h = regla.get("holgura")
    if isinstance(h, (int, float)) and h > 0:
        return Fraction(str(h))
    return MEDIO


def aritmeticas(doc, ambiente, fecha):
    """Resultado de cada regla aritmética vigente que aplica al documento: 'pasa' o 'falla'.

    Las reglas sin verificación posible (conformidad/cobertura.json) no se evalúan.
    """
    excluidas = sin_caso()
    resultado = {}
    for r in REGLAS.values():
        if r["tipo"] != "aritmetica" or r.get("descartada") or r["id"] in excluidas:
            continue
        if not vigente(r, ambiente, fecha):
            continue
        if not doc.todos(r["campo"]):
            continue
        for n in doc.todos(r["campo"]):
            if r.get("condicion") and not cumple(doc, n, r["condicion"]):
                continue
            if r["id"] not in REFERENCIA:
                raise SystemExit(f"{r['id']} aplica pero no tiene implementación de referencia: agregala o "
                                 "registrála en conformidad/cobertura.json con el motivo")
            try:
                esperado = REFERENCIA[r["id"]](doc, n)
            except (NoCalculable, ZeroDivisionError):
                continue
            if isinstance(esperado, bool):
                ok = esperado
            else:
                informado = decimal(n.texto)
                ok = informado is not None and abs(informado - esperado) <= tolerancia(r)
            if not ok:
                resultado[r["id"]] = "falla"
            else:
                resultado.setdefault(r["id"], "pasa")
    return resultado


def esperado_aritmetico(doc, ambiente, fecha, otras, xsd=True, extra_fallan=()):
    res = aritmeticas(doc, ambiente, fecha)
    fallan = [{"regla": rid, "campo": REGLAS[rid]["campo"]} for rid in sorted(res) if res[rid] == "falla"]
    fallan += [{"regla": rid, "campo": REGLAS[rid]["campo"]} for rid in extra_fallan]
    return {
        "xsd": xsd,
        "fallan": sorted(fallan, key=lambda f: f["regla"]),
        "pasan": sorted(rid for rid in res if res[rid] == "pasa"),
        "otras": otras,
    }


# --- mutaciones --------------------------------------------------------------------------------------------------

def mas_uno(texto):
    """Suma una unidad conservando la cantidad de decimales del texto (9.09 -> 10.09, 110.00 -> 111.00)."""
    d = Decimal(texto)
    return str((d + 1).quantize(d)) if d.as_tuple().exponent < 0 else str(d + 1)


def fecha_menos_un_dia(texto):
    return (datetime.datetime.fromisoformat(texto) - datetime.timedelta(days=1)).isoformat()


def numero_7(n):
    return f"{n:07d}"


# Cambios que no son "+1": reglas de rango y de fechas de los eventos.
MUTACIONES = {
    "R-GEI006-A1": ("GEI006", lambda doc, n: numero_7(entero(doc, n, "GEI005") + 1001),
                    "el rango pasa a tener 1001 números más que el inicio"),
    "R-GEI006-A2": ("GEI006", lambda doc, n: contexto(doc, n, "GEI005")[0].texto,
                    "el final del rango queda igual al inicio"),
    "R-GEI006-A3": ("GEI006", lambda doc, n: numero_7(entero(doc, n, "GEI005") + 1000),
                    "el rango pasa a tener 1001 números"),
    "R-GEN004-A1": ("GEN004", lambda doc, n: fecha_menos_un_dia(contexto(doc, n, "GEN003")[0].texto),
                    "la fecha de recepción queda un día antes de la de emisión"),
    "R-GED004-A1": ("GED004", lambda doc, n: fecha_menos_un_dia(contexto(doc, n, "GED003")[0].texto),
                    "la fecha de recepción queda un día antes de la de emisión"),
}

# Documento base preferido para la falla de una regla, cuando hay otro con menos reglas afectadas.
BASE_PREFERIDA = {"R-F014-A1": "autofactura"}


def cdc_dv(base43):
    total, peso = 0, 2
    for ch in reversed(base43):
        total += int(ch) * peso
        peso = 2 if peso == 11 else peso + 1
    resto = total % 11
    return "0" if resto <= 1 else str(11 - resto)


def cambiar_fecha(doc, fecha):
    """Mueve la fecha de emisión y de firma de un DE y recalcula su CDC (que incluye la fecha)."""
    for fid in ("D002", "A004"):
        for n in doc.todos(fid):
            n.elem.text = fecha + n.elem.text[10:]
    de = doc.todos("A001")[0].elem
    cdc = de.get("Id")
    nuevo = cdc[:25] + fecha.replace("-", "") + cdc[33:43]
    nuevo += cdc_dv(nuevo)
    de.set("Id", nuevo)
    doc.todos("A003")[0].elem.text = nuevo[-1]


def quitar(doc, fids):
    """Quita los elementos de esos campos y devuelve el documento que queda."""
    for fid in fids:
        for n in doc.todos(fid):
            n.padre.elem.remove(n.elem)
    return Documento(doc.raiz_elem)


# --- casos -------------------------------------------------------------------------------------------------------

def ruta_base(nombre):
    return os.path.join(CONF, "bases", nombre + ".xml")


def caso(tipo, descripcion, base, xml, evaluaciones, **extra):
    c = {"tipo": tipo, "descripcion": descripcion, "base": base, "xml": xml}
    c.update(extra)
    c["evaluaciones"] = evaluaciones
    return c


def casos_validos(salida):
    for nombre, descripcion in BASES:
        doc = leer(ruta_base(nombre))
        fecha = doc.fecha()
        esperado = esperado_aritmetico(doc, "test", fecha, "prohibidas")
        if esperado["fallan"]:
            raise SystemExit(f"la base {nombre} no cumple {esperado['fallan']}")
        with open(ruta_base(nombre), encoding="utf-8") as fh:
            texto = fh.read()
        salida[f"validacion/{nombre}-valido"] = (
            caso("validacion", f"{descripcion}, válido: cumple todas las reglas que le aplican",
                 nombre, f"{nombre}-valido.xml",
                 [{"ambiente": "test", "fecha": fecha, "esperado": esperado}]),
            {f"{nombre}-valido.xml": texto})


def bases_por_regla():
    """Para cada regla aritmética, la primera base (en el orden de BASES) donde aplica y se cumple."""
    out = {}
    for nombre, _ in BASES:
        doc = leer(ruta_base(nombre))
        for rid, res in aritmeticas(doc, "test", doc.fecha()).items():
            if res == "pasa":
                out.setdefault(rid, [])
                out[rid].append(nombre)
    return out


def casos_aritmeticos(salida):
    # Las reglas vigentes en la fecha de los documentos base: la salida no depende del día en que se genera.
    fecha_bases = leer(ruta_base("factura")).fecha()
    por_regla = bases_por_regla()
    for rid in sorted(reglas_a_cubrir(fecha_bases)):
        candidatas = por_regla.get(rid)
        if not candidatas:
            raise SystemExit(f"{rid}: ningún documento base la cumple; agregá uno o registrála en cobertura.json")
        base = BASE_PREFERIDA.get(rid) if BASE_PREFERIDA.get(rid) in candidatas else candidatas[0]
        doc = leer(ruta_base(base))
        fecha = doc.fecha()
        regla = REGLAS[rid]
        objetivo = next(n for n in doc.todos(regla["campo"])
                        if not regla.get("condicion") or cumple(doc, n, regla["condicion"]))
        antes = objetivo.texto
        if rid in MUTACIONES:
            _, cambio, como = MUTACIONES[rid]
            despues = cambio(doc, objetivo)
        else:
            despues, como = mas_uno(antes), "se suma una unidad al valor informado"
        ruta = objetivo.ruta()
        objetivo.elem.text = despues
        esperado = esperado_aritmetico(doc, "test", fecha, "prohibidas")
        if rid not in [f["regla"] for f in esperado["fallan"]]:
            raise SystemExit(f"{rid}: la mutación no la hace fallar")
        nombre = f"{base}-{rid.lower()}"
        salida[f"aritmetica/{nombre}"] = (
            caso("aritmetica",
                 f"{regla['texto']}. Falla: {como} ({regla['campo']})",
                 base, f"{nombre}.xml",
                 [{"ambiente": "test", "fecha": fecha, "esperado": esperado}],
                 regla=rid,
                 cambio={"campo": regla["campo"], "ruta": ruta, "antes": antes, "despues": despues}),
            {f"{nombre}.xml": escribir_xml(doc)})


def reglas_a_cubrir(fecha):
    """Reglas aritméticas vigentes en la fecha (en algún ambiente), no descartadas y con verificación posible."""
    excluidas = sin_caso()
    return {r["id"] for r in REGLAS.values()
            if r["tipo"] == "aritmetica" and not r.get("descartada") and r["id"] not in excluidas
            and (vigente(r, "test", fecha) or vigente(r, "produccion", fecha))}


# Faltas de presencia: un campo que una regla exige y el XSD permite omitir (xsd: true), o que el XSD también exige.
PRESENCIA = [
    ("factura", ["EA003"], "R-EA003-C1", True,
     "falta el porcentaje de descuento particular (EA003) de un ítem con descuento (EA002 > 0)"),
    ("factura", ["D206"], "R-D206-C1", True,
     "falta el RUC del receptor contribuyente (D201 = 1)"),
    ("factura", ["E010"], "R-E010-C1", True,
     "falta el grupo de campos de la factura electrónica (E010) en una factura (C002 = 1)"),
    ("autofactura", ["D011", "D012"], "R-D011-C1", True,
     "faltan el tipo de transacción (D011) y su descripción en una autofactura (C002 = 4)"),
    ("evento-actualizacion-transporte", ["GET004", "GET005"], "R-GET004-C1", True,
     "falta el departamento del local de entrega (GET004) con cambio de local de entrega (GET003 = 1)"),
    ("evento-notificacion-recepcion", ["GEN007"], "R-GEN007-C1", True,
     "falta el RUC del receptor contribuyente (GEN005 = 1)"),
]


def casos_presencia(salida):
    for base, quitados, rid, xsd, como in PRESENCIA:
        regla = REGLAS[rid]
        doc = leer(ruta_base(base))
        fecha = doc.fecha()
        if regla["campo"] not in quitados or not doc.todos(regla["campo"]):
            raise SystemExit(f"{rid}: el caso debe quitar el campo {regla['campo']}, presente en la base")
        if not vigente(regla, "test", fecha) or regla["tipo"] not in ("obligatorio", "condicional"):
            raise SystemExit(f"{rid}: no es una regla de presencia vigente")
        padre = doc.todos(regla["campo"])[0].padre
        if regla.get("condicion") and not cumple(doc, padre, regla["condicion"]):
            raise SystemExit(f"{rid}: la condición no se cumple en la base")
        doc = quitar(doc, quitados)
        nombre = f"{base}-sin-{regla['campo'].lower()}"
        esperado = esperado_aritmetico(doc, "test", fecha, "prohibidas", xsd=xsd, extra_fallan=[rid])
        salida[f"validacion/{nombre}"] = (
            caso("validacion", f"{regla['texto']}. Falla: {como}", base, f"{nombre}.xml",
                 [{"ambiente": "test", "fecha": fecha, "esperado": esperado}],
                 regla=rid, quitados=quitados),
            {f"{nombre}.xml": escribir_xml(doc)})


# Vigencia: la factura base (con un ítem gravado parcial) en la transición de la NT 13 (fórmulas de E735, E737,
# F002, F004 y F005), que entró en vigor el 2023-04-21 en test y el 2023-06-17 en producción.
VIGENCIA = [
    ("factura-nt13-mismo-dia-dos-ambientes",
     "La misma factura del 2023-05-02 con un ítem gravado parcial: en test ya rigen las fórmulas de la NT 13 "
     "(se cumplen); en producción todavía rigen las anteriores (R-E735-A3, R-F002-A1, R-F005-A1), que no se cumplen",
     [("test", "2023-05-02"), ("produccion", "2023-05-02")]),
    ("factura-nt13-test-antes-y-despues",
     "La misma factura en test el día anterior a la NT 13 (2023-04-20, rigen las fórmulas anteriores) y el día "
     "de entrada en vigor (2023-04-21, rigen las nuevas: el `hasta` excluye su fecha)",
     [("test", "2023-04-20"), ("test", "2023-04-21")]),
    ("factura-nt13-produccion-antes-y-despues",
     "La misma factura en producción el día anterior a la NT 13 (2023-06-16) y el día de entrada en vigor "
     "(2023-06-17)",
     [("produccion", "2023-06-16"), ("produccion", "2023-06-17")]),
]


def casos_vigencia(salida):
    for nombre, descripcion, evaluaciones in VIGENCIA:
        archivos, evs = {}, []
        fechas = sorted({f for _, f in evaluaciones})
        for ambiente, fecha in evaluaciones:
            doc = leer(ruta_base("factura"))
            cambiar_fecha(doc, fecha)
            xml = f"{nombre}.xml" if len(fechas) == 1 else f"{nombre}-{fecha}.xml"
            archivos[xml] = escribir_xml(doc)
            ev = {"ambiente": ambiente, "fecha": fecha}
            if len(fechas) > 1:
                ev["xml"] = xml
            ev["esperado"] = esperado_aritmetico(doc, ambiente, fecha, "permitidas")
            evs.append(ev)
        resultados = [tuple(f["regla"] for f in e["esperado"]["fallan"]) for e in evs]
        if len(set(resultados)) < 2:
            raise SystemExit(f"{nombre}: las evaluaciones no difieren")
        salida[f"vigencia/{nombre}"] = (
            caso("vigencia", descripcion, "factura", next(iter(archivos)) if len(fechas) == 1 else None, evs,
                 notas="Solo se fijan las reglas aritméticas (fallan y pasan): en 2023 pueden regir otros "
                       "catálogos y campos, por eso se permiten otras observaciones."),
            archivos)


# --- respuestas ----------------------------------------------------------------------------------------------------

SOBRE = ('<?xml version="1.0" encoding="UTF-8"?>\n<env:Envelope xmlns:env="http://www.w3.org/2003/05/soap-envelope">'
         '<env:Header/><env:Body>{}</env:Body></env:Envelope>\n')
CDC_FACTURA = None  # se completa con el CDC de la factura base


def grupo_res(codigo, mensaje):
    return f"<ns2:gResProc><ns2:dCodRes>{codigo}</ns2:dCodRes><ns2:dMsgRes>{mensaje}</ns2:dMsgRes></ns2:gResProc>"


def mensaje(codigo, servicios):
    for s in servicios:
        if (codigo, s) in RESPUESTAS:
            return RESPUESTAS[(codigo, s)]
    raise SystemExit(f"código {codigo} inexistente en respuestas/ para {servicios}")


SERVICIOS_RECEPCION = ("recepcion", "formato-de", "generico", "certificado")
SERVICIOS_EVENTO = ("evento", "formato-evento", "generico", "certificado")

ESTADOS = {"Aprobado": "aprobado", "Aprobado con observación": "aprobado_con_observacion", "Rechazado": "rechazado"}

RESPUESTAS_CASOS = [
    ("recepcion-aprobado", "recepcion", "Recepción síncrona de un DE aprobado",
     [("Aprobado", "1234567890", ["0260"])]),
    ("recepcion-aprobado-con-observacion", "recepcion",
     "Recepción síncrona de un DE aprobado con observación (transmisión extemporánea)",
     [("Aprobado con observación", "1234567891", ["1005"])]),
    ("recepcion-rechazado-varios-codigos", "recepcion",
     "Recepción síncrona de un DE rechazado por cálculos incorrectos, con varios códigos en orden",
     [("Rechazado", None, ["1859", "2369", "2365"])]),
    ("evento-aprobado", "evento", "Recepción de un evento aprobado",
     [("Aprobado", "1234567892", ["0600"])]),
    ("evento-mixto", "evento", "Recepción de dos eventos: uno aprobado y otro rechazado",
     [("Aprobado", "1234567893", ["0600"]), ("Rechazado", None, ["4003"])]),
]


def casos_respuestas(salida):
    cdc = leer(ruta_base("factura")).todos("A001")[0].elem.get("Id")
    for nombre, servicio, descripcion, resultados in RESPUESTAS_CASOS:
        servicios = SERVICIOS_RECEPCION if servicio == "recepcion" else SERVICIOS_EVENTO
        esperados = []
        if servicio == "recepcion":
            estado, protocolo, codigos = resultados[0]
            cuerpo = (f'<ns2:rRetEnviDe xmlns:ns2="{NS}"><ns2:rProtDe><ns2:Id>{cdc}</ns2:Id>'
                      "<ns2:dFecProc>2026-11-20T10:00:05-03:00</ns2:dFecProc>"
                      "<ns2:dDigVal>UHJ1ZWJhIHNpbnRldGljYSBkZSBkaWdlc3Q=</ns2:dDigVal>"
                      f"<ns2:dEstRes>{estado}</ns2:dEstRes>"
                      + (f"<ns2:dProtAut>{protocolo}</ns2:dProtAut>" if protocolo else "")
                      + "".join(grupo_res(c, mensaje(c, servicios)["mensaje"]) for c in codigos)
                      + "</ns2:rProtDe></ns2:rRetEnviDe>")
            ids = [cdc]
        else:
            grupos, ids = [], []
            for i, (estado, protocolo, codigos) in enumerate(resultados, start=1):
                ids.append(str(i))
                grupos.append(f"<ns2:gResProcEVe><ns2:dEstRes>{estado}</ns2:dEstRes>"
                              + (f"<ns2:dProtAut>{protocolo}</ns2:dProtAut>" if protocolo else "")
                              + f"<ns2:id>{i}</ns2:id>"
                              + "".join(grupo_res(c, mensaje(c, servicios)["mensaje"]) for c in codigos)
                              + "</ns2:gResProcEVe>")
            cuerpo = (f'<ns2:rRetEnviEventoDe xmlns:ns2="{NS}"><ns2:dFecProc>2026-11-20T11:00:05-03:00</ns2:dFecProc>'
                      + "".join(grupos) + "</ns2:rRetEnviEventoDe>")
        for ident, (estado, protocolo, codigos) in zip(ids, resultados):
            esperados.append({
                "id": ident,
                "estado": ESTADOS[estado],
                "protocolo": protocolo,
                "mensajes": [{"codigo": c, "clase": mensaje(c, servicios)["clase"]} for c in codigos],
            })
        entrada = {"servicio": servicio}
        if servicio == "recepcion":
            entrada["cdc"] = cdc
        salida[f"respuestas/{nombre}"] = (
            {"tipo": "respuestas", "descripcion": descripcion, "xml": f"{nombre}.xml", "entrada": entrada,
             "esperado": {"resultados": esperados}},
            {f"{nombre}.xml": SOBRE.format(cuerpo)})


# --- salida ------------------------------------------------------------------------------------------------------

def generar():
    salida = {}
    casos_validos(salida)
    casos_presencia(salida)
    casos_aritmeticos(salida)
    casos_vigencia(salida)
    casos_respuestas(salida)
    archivos = {}
    for clave, (c, xmls) in salida.items():
        if c.get("xml") is None:
            c.pop("xml")
        carpeta = os.path.dirname(clave)
        archivos[os.path.join(carpeta, os.path.basename(clave) + ".json")] = (
            json.dumps(c, ensure_ascii=False, indent=2) + "\n")
        for nombre, texto in xmls.items():
            archivos[os.path.join(carpeta, nombre)] = texto if texto.endswith("\n") else texto + "\n"
    return archivos


def existentes():
    out = set()
    for tipo in TIPOS_GENERADOS:
        for ruta in glob.glob(os.path.join(CONF, tipo, "*")):
            out.add(os.path.relpath(ruta, CONF))
    return out


def main():
    archivos = generar()
    if "--verificar" in sys.argv:
        diferencias = []
        for rel, texto in archivos.items():
            ruta = os.path.join(CONF, rel)
            if not os.path.exists(ruta) or open(ruta, encoding="utf-8").read() != texto:
                diferencias.append(f"conformidad/{rel}: no está al día")
        for rel in sorted(existentes() - set(archivos)):
            diferencias.append(f"conformidad/{rel}: sobra (no lo genera tools/generar_conformidad.py)")
        if diferencias:
            print("\n".join(sorted(diferencias)))
            print("Corré python3 tools/generar_conformidad.py")
            return 1
        print(f"OK: {len(archivos)} archivos de conformidad al día")
        return 0
    for rel in existentes() - set(archivos):
        os.remove(os.path.join(CONF, rel))
    for rel, texto in archivos.items():
        ruta = os.path.join(CONF, rel)
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
    n = sum(1 for rel in archivos if rel.endswith(".json"))
    print(f"OK: {n} casos generados en conformidad/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
