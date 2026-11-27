#!/usr/bin/env python3
"""Verifica la batería de conformidad.

Uso:  python3 tools/conformidad.py         formato de cada caso, coherencia con las reglas y cobertura
      python3 tools/conformidad.py --xsd   además valida los XML contra el XSD oficial (necesita lxml)

- CDC y QR: recalcula el resultado esperado.
- Validación, aritmética y vigencia: el formato del caso; que la fecha sea la del documento; que las reglas
  existan, rijan ese día en ese ambiente y apunten a su campo; y que lo que se espera de las reglas aritméticas
  coincida con la implementación de referencia de tools/generar_conformidad.py.
- Respuestas: el formato, que el XML diga lo mismo que el resultado esperado y que cada código exista en
  respuestas/ con esa clase.
- Cobertura: toda regla aritmética vigente hoy y no descartada tiene un caso que la cumple y uno que la viola, salvo
  las registradas con su motivo en conformidad/cobertura.json.
- Que los casos generados estén al día con tools/generar_conformidad.py.

Es una implementación de referencia mínima, solo para comprobar que los casos son coherentes. No es un SDK. Sin
dependencias, salvo --xsd: biblioteca estándar de Python 3.
"""
import datetime
import glob
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import generar_conformidad as gen  # noqa: E402

RAIZ = gen.RAIZ
CONF = gen.CONF
QR_BASE = {
    "produccion": "https://ekuatia.set.gov.py/consultas/qr?",
    "test": "https://ekuatia.set.gov.py/consultas-test/qr?",
}
ORDEN_CDC = [
    "tipoDocumento", "rucEmisor", "digitoVerificadorRuc", "establecimiento", "puntoExpedicion", "numeroDocumento",
    "tipoContribuyente", "fechaEmision", "tipoEmision", "codigoSeguridad",
]
ORDEN_QR = ["nVersion", "Id", "dFeEmiDE", "dRucRec", "dTotGralOpe", "dTotIVA", "cItems", "DigestValue", "IdCSC"]
FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AMBIENTES = {"test", "produccion"}
OTRAS = {"prohibidas", "permitidas"}
PRESENCIA = {"obligatorio", "condicional"}
ESTADOS = {"aprobado", "aprobado_con_observacion", "rechazado", "en_proceso"}
SERVICIOS = {"recepcion": gen.SERVICIOS_RECEPCION, "evento": gen.SERVICIOS_EVENTO}
fallas = []


def falla(ruta, msg):
    fallas.append(f"{os.path.relpath(ruta, RAIZ)}: {msg}")


def modulo11(digitos):
    """Dígito verificador módulo 11 con pesos 2 a 11 desde la derecha."""
    return gen.cdc_dv(digitos)


def caso_cdc(c):
    base = "".join(c["entrada"][k] for k in ORDEN_CDC)
    dv = modulo11(base)
    cdc = base + dv
    kude = " ".join(cdc[i:i + 4] for i in range(0, len(cdc), 4))
    return {"cdc": cdc, "digitoVerificador": dv, "representacionKude": kude}


def caso_qr(c):
    e = dict(c["entrada"])
    e["dFeEmiDE"] = e["dFeEmiDE"].encode("utf-8").hex()
    e["DigestValue"] = e["DigestValue"].encode("utf-8").hex()
    datos = "&".join(f"{k}={e[k]}" for k in ORDEN_QR)
    h = hashlib.sha256((datos + e["CSC"]).encode("utf-8")).hexdigest()
    url = QR_BASE[e["ambiente"]] + datos + "&cHashQR=" + h
    return {"datos": datos, "cHashQR": h, "url": url, "dCarQR": url.replace("&", "&amp;")}


def verificar_calculable(ruta, c):
    obtenido = {"cdc": caso_cdc, "qr": caso_qr}[c["tipo"]](c)
    for clave, esperado in c["esperado"].items():
        if obtenido.get(clave) != esperado:
            falla(ruta, f"{clave}: esperado {esperado!r}, obtenido {obtenido.get(clave)!r}")


# --- validación, aritmética y vigencia ---------------------------------------------------------------------------

def verificar_documento(ruta, c, cobertura_fallan, cobertura_pasan):
    carpeta = os.path.dirname(ruta)
    if not str(c.get("descripcion", "")).strip():
        falla(ruta, "falta 'descripcion'")
    if not os.path.exists(gen.ruta_base(str(c.get("base")))):
        falla(ruta, f"'base' no es un documento de conformidad/bases: {c.get('base')!r}")
    evaluaciones = c.get("evaluaciones")
    if not isinstance(evaluaciones, list) or not evaluaciones:
        falla(ruta, "falta 'evaluaciones' (lista no vacía)")
        return
    if c["tipo"] in ("validacion", "aritmetica") and len(evaluaciones) != 1:
        falla(ruta, f"un caso de {c['tipo']} lleva una sola evaluación")
    if c["tipo"] == "vigencia" and len(evaluaciones) < 2:
        falla(ruta, "un caso de vigencia lleva al menos dos evaluaciones")
    resultados, fallan = set(), {}
    for i, ev in enumerate(evaluaciones):
        donde = f"evaluaciones[{i}]"
        xml = ev.get("xml", c.get("xml"))
        if "xml" in ev and c["tipo"] != "vigencia":
            falla(ruta, f"{donde}: solo los casos de vigencia indican un 'xml' por evaluación")
        if not xml or not os.path.exists(os.path.join(carpeta, xml)):
            falla(ruta, f"{donde}: no existe el XML {xml!r} junto al caso")
            continue
        try:
            doc = gen.leer(os.path.join(carpeta, xml))
        except (ET.ParseError, ValueError) as e:
            falla(ruta, f"{donde}: XML ilegible: {e}")
            continue
        ambiente, fecha, esperado = ev.get("ambiente"), ev.get("fecha"), ev.get("esperado")
        if ambiente not in AMBIENTES:
            falla(ruta, f"{donde}: 'ambiente' debe ser test o produccion")
        if not FECHA.match(str(fecha)):
            falla(ruta, f"{donde}: 'fecha' debe ser AAAA-MM-DD")
            continue
        if doc.fecha() != fecha:
            falla(ruta, f"{donde}: 'fecha' ({fecha}) no es la del documento ({doc.fecha()}, "
                        f"{gen.CAMPO_FECHA[doc.tipo]})")
        if not isinstance(esperado, dict) or set(esperado) != {"xsd", "fallan", "pasan", "otras"}:
            falla(ruta, f"{donde}: 'esperado' lleva exactamente xsd, fallan, pasan y otras")
            continue
        if not isinstance(esperado["xsd"], bool):
            falla(ruta, f"{donde}: 'xsd' es true o false")
        if esperado["otras"] not in OTRAS:
            falla(ruta, f"{donde}: 'otras' es prohibidas o permitidas")
        fallan = {}
        for f in esperado["fallan"]:
            regla = gen.REGLAS.get(f.get("regla")) if isinstance(f, dict) else None
            if regla is None or set(f) != {"regla", "campo"}:
                falla(ruta, f"{donde}: cada falla lleva 'regla' (existente) y 'campo': {f!r}")
                continue
            if f["campo"] != regla["campo"]:
                falla(ruta, f"{donde}: {f['regla']} es del campo {regla['campo']}, no de {f['campo']}")
            if not gen.vigente(regla, ambiente, fecha):
                falla(ruta, f"{donde}: {f['regla']} no rige el {fecha} en {ambiente}")
            if regla.get("descartada"):
                falla(ruta, f"{donde}: {f['regla']} está descartada: los SDK no la verifican")
            fallan[f["regla"]] = regla
        pasan = esperado["pasan"]
        for rid in pasan:
            if rid not in gen.REGLAS:
                falla(ruta, f"{donde}: regla inexistente en 'pasan': {rid!r}")
        if set(pasan) & set(fallan):
            falla(ruta, f"{donde}: una regla no puede fallar y pasar a la vez: {sorted(set(pasan) & set(fallan))}")
        if len(set(pasan)) != len(pasan) or len(fallan) != len(esperado["fallan"]):
            falla(ruta, f"{donde}: reglas repetidas")
        # Lo aritmético coincide con la implementación de referencia.
        ref = gen.aritmeticas(doc, ambiente, fecha)
        esperadas = {rid for rid, r in fallan.items() if r["tipo"] == "aritmetica"}
        calculadas = {rid for rid, res in ref.items() if res == "falla"}
        if esperadas != calculadas:
            falla(ruta, f"{donde}: las reglas aritméticas que fallan según la referencia son {sorted(calculadas)}, "
                        f"no {sorted(esperadas)}")
        if set(pasan) != {rid for rid, res in ref.items() if res == "pasa"}:
            falla(ruta, f"{donde}: 'pasan' no coincide con las reglas aritméticas que se cumplen según la referencia")
        # Las faltas de presencia: el campo no está y la regla lo exige.
        for rid, regla in fallan.items():
            if regla["tipo"] == "aritmetica":
                continue
            if regla["tipo"] not in PRESENCIA:
                falla(ruta, f"{donde}: {rid}: solo hay casos de reglas aritméticas y de presencia")
            elif doc.todos(regla["campo"]):
                falla(ruta, f"{donde}: {rid}: el campo {regla['campo']} está en el documento")
        for rid in fallan:
            cobertura_fallan.add(rid)
        for rid in pasan:
            cobertura_pasan.add(rid)
        resultados.add(tuple(sorted(fallan)))
    if c["tipo"] == "vigencia" and len(resultados) < 2:
        falla(ruta, "en un caso de vigencia las evaluaciones esperan resultados distintos")
    if c["tipo"] == "aritmetica":
        if c.get("regla") not in fallan:
            falla(ruta, "un caso aritmético indica en 'regla' la regla que viola, y esa regla está en 'fallan'")
        if not isinstance(c.get("cambio"), dict):
            falla(ruta, "un caso aritmético describe en 'cambio' el valor que se modificó")


# --- respuestas ----------------------------------------------------------------------------------------------------

def texto(elem, nombre):
    e = elem.find(f"{{{gen.NS}}}{nombre}")
    return None if e is None else e.text


def verificar_respuesta(ruta, c):
    carpeta = os.path.dirname(ruta)
    entrada, esperado = c.get("entrada") or {}, c.get("esperado") or {}
    servicio = entrada.get("servicio")
    if servicio not in SERVICIOS:
        falla(ruta, "entrada.servicio es recepcion o evento")
        return
    xml = os.path.join(carpeta, str(c.get("xml")))
    if not os.path.exists(xml):
        falla(ruta, f"no existe el XML {c.get('xml')!r} junto al caso")
        return
    cuerpo = ET.parse(xml).getroot().find("{http://www.w3.org/2003/05/soap-envelope}Body")
    raiz = cuerpo[0] if cuerpo is not None and len(cuerpo) else None
    if servicio == "recepcion":
        if raiz is None or raiz.tag != f"{{{gen.NS}}}rRetEnviDe":
            falla(ruta, "la respuesta de recepción es un rRetEnviDe dentro del sobre SOAP")
            return
        grupos = raiz.findall(f"{{{gen.NS}}}rProtDe")
        ids = [texto(g, "Id") for g in grupos]
        if ids != [entrada.get("cdc")]:
            falla(ruta, "rProtDe/Id debe ser el CDC de entrada.cdc")
    else:
        if raiz is None or raiz.tag != f"{{{gen.NS}}}rRetEnviEventoDe":
            falla(ruta, "la respuesta de eventos es un rRetEnviEventoDe dentro del sobre SOAP")
            return
        grupos = raiz.findall(f"{{{gen.NS}}}gResProcEVe")
        ids = [texto(g, "id") for g in grupos]
    resultados = esperado.get("resultados")
    if not isinstance(resultados, list) or len(resultados) != len(grupos):
        falla(ruta, "esperado.resultados lleva un resultado por documento o evento de la respuesta")
        return
    for ident, g, r in zip(ids, grupos, resultados):
        if r.get("id") != ident:
            falla(ruta, f"resultado {r.get('id')!r}: el XML dice {ident!r}")
        if r.get("estado") not in ESTADOS or gen.ESTADOS.get(texto(g, "dEstRes")) != r.get("estado"):
            falla(ruta, f"resultado {ident}: el estado no coincide con dEstRes {texto(g, 'dEstRes')!r}")
        if r.get("protocolo") != texto(g, "dProtAut"):
            falla(ruta, f"resultado {ident}: el protocolo no coincide con dProtAut")
        codigos = [texto(m, "dCodRes") for m in g.findall(f"{{{gen.NS}}}gResProc")]
        if [m.get("codigo") for m in r.get("mensajes", [])] != codigos:
            falla(ruta, f"resultado {ident}: los códigos no coinciden con los gResProc, en orden")
        for m in r.get("mensajes", []):
            try:
                ref = gen.mensaje(m.get("codigo"), SERVICIOS[servicio])
            except SystemExit:
                falla(ruta, f"código {m.get('codigo')!r} inexistente en respuestas/ para {servicio}")
                continue
            if m.get("clase") != ref["clase"]:
                falla(ruta, f"código {m['codigo']}: la clase en respuestas/ es {ref['clase']!r}")


# --- XSD (opcional) ------------------------------------------------------------------------------------------------

def validador_xsd():
    from lxml import etree

    oficial = os.path.join(RAIZ, "xsd", "oficial")

    class Local(etree.Resolver):
        def resolve(self, url, pubid, context):
            nombre = url.rsplit("/", 1)[-1]
            if os.path.exists(os.path.join(oficial, nombre)):
                return self.resolve_filename(os.path.join(oficial, nombre), context)
            return None

    def esquema(incluido, declaraciones):
        texto_xsd = (f'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns="{gen.NS}" '
                     f'targetNamespace="{gen.NS}" elementFormDefault="qualified">'
                     f'<xs:include schemaLocation="https://ekuatia.set.gov.py/sifen/xsd/{incluido}"/>'
                     f"{declaraciones}</xs:schema>")
        parser = etree.XMLParser(no_network=True)
        parser.resolvers.add(Local())
        raiz = etree.fromstring(texto_xsd.encode("utf-8"), parser,
                               base_url=os.path.join(oficial, "envoltorio.xsd"))
        return etree.XMLSchema(raiz)

    de = esquema("DE_v150.xsd", '<xs:element name="DE" type="tDE"/>')
    eve = esquema("Evento_v150.xsd", '<xs:element name="rEve" type="trEve"/>')

    def oficial_ws(nombre):
        parser = etree.XMLParser(no_network=True)
        parser.resolvers.add(Local())
        return etree.XMLSchema(etree.parse(os.path.join(oficial, nombre), parser))

    ws = {"recepcion": oficial_ws("WS_SiRecepDE_v150.xsd"), "evento": oficial_ws("WS_SiRecepEvento_v150.xsd")}

    def valida(ruta_xml, servicio=None):
        arbol = etree.parse(ruta_xml)
        raiz = arbol.getroot()
        if servicio:
            esquema_ws = ws[servicio]
            cuerpo = raiz.find("{http://www.w3.org/2003/05/soap-envelope}Body")[0]
            return esquema_ws.validate(etree.ElementTree(cuerpo)), esquema_ws.error_log
        if raiz.tag == f"{{{gen.NS}}}rDE":
            return de.validate(etree.ElementTree(raiz.find(f"{{{gen.NS}}}DE"))), de.error_log
        return eve.validate(etree.ElementTree(raiz.find(f"{{{gen.NS}}}rEve"))), eve.error_log

    return valida


def verificar_xsd(casos):
    try:
        valida = validador_xsd()
    except ImportError:
        print("--xsd necesita lxml (pip install lxml)")
        return False
    total = 0
    for ruta in sorted(glob.glob(os.path.join(CONF, "bases", "*.xml"))):
        ok, log = valida(ruta)
        total += 1
        if not ok:
            falla(ruta, f"no valida contra el XSD: {log.last_error}")
    for ruta, c in casos:
        carpeta = os.path.dirname(ruta)
        if c["tipo"] == "respuestas":
            ok, log = valida(os.path.join(carpeta, c["xml"]), c["entrada"]["servicio"])
            total += 1
            if not ok:
                falla(ruta, f"la respuesta no valida contra el XSD: {log.last_error}")
            continue
        for ev in c["evaluaciones"]:
            ok, log = valida(os.path.join(carpeta, ev.get("xml", c.get("xml"))))
            total += 1
            if ok != ev["esperado"]["xsd"]:
                falla(ruta, f"se espera xsd={ev['esperado']['xsd']} y el XSD dice {ok}: {log.last_error}")
    print(f"OK: {total} XML contra el XSD oficial")
    return True


# --- principal -----------------------------------------------------------------------------------------------------

def main():
    total = 0
    casos = []
    cubiertas_fallan, cubiertas_pasan = set(), set()
    for ruta in sorted(glob.glob(os.path.join(CONF, "*", "*.json"))):
        try:
            c = gen.cargar_json(ruta)
        except ValueError as e:
            falla(ruta, f"no es JSON válido: {e}")
            continue
        tipo = c.get("tipo")
        carpeta = os.path.basename(os.path.dirname(ruta))
        if tipo != carpeta:
            falla(ruta, f"el tipo {tipo!r} no coincide con la carpeta {carpeta!r}")
            continue
        total += 1
        if tipo in ("cdc", "qr"):
            verificar_calculable(ruta, c)
        elif tipo in ("validacion", "aritmetica", "vigencia"):
            verificar_documento(ruta, c, cubiertas_fallan, cubiertas_pasan)
            casos.append((ruta, c))
        elif tipo == "respuestas":
            verificar_respuesta(ruta, c)
            casos.append((ruta, c))
        else:
            falla(ruta, f"tipo de caso desconocido {tipo!r}")

    # Cobertura de las reglas aritméticas.
    ruta_cob = os.path.join(CONF, "cobertura.json")
    for e in gen.cobertura()["aritmetica_sin_caso"]:
        r = gen.REGLAS.get(e.get("regla"))
        if r is None or r["tipo"] != "aritmetica" or r.get("descartada"):
            falla(ruta_cob, f"{e.get('regla')!r}: no es una regla aritmética vigente sin descartar")
        if not str(e.get("motivo", "")).strip():
            falla(ruta_cob, f"{e.get('regla')}: falta el 'motivo'")
    hoy = datetime.date.today().isoformat()
    a_cubrir = gen.reglas_a_cubrir(hoy)
    for rid in sorted(a_cubrir - cubiertas_fallan):
        falla(ruta_cob, f"{rid}: regla aritmética vigente sin un caso que la viole")
    for rid in sorted(a_cubrir - cubiertas_pasan):
        falla(ruta_cob, f"{rid}: regla aritmética vigente sin un caso que la cumpla")

    # Los casos generados están al día.
    archivos = gen.generar()
    for rel, contenido in archivos.items():
        ruta = os.path.join(CONF, rel)
        if not os.path.exists(ruta) or open(ruta, encoding="utf-8").read() != contenido:
            falla(ruta, "no está al día: corré python3 tools/generar_conformidad.py")
    for rel in sorted(gen.existentes() - set(archivos)):
        falla(os.path.join(CONF, rel), "sobra: no lo genera tools/generar_conformidad.py")

    if "--xsd" in sys.argv and not verificar_xsd(casos):
        return 2
    if fallas:
        print("\n".join(fallas))
        print(f"\n{len(fallas)} problema(s)")
        return 1
    print(f"OK: {total} casos de conformidad verificados; {len(a_cubrir)} reglas aritméticas vigentes con un caso "
          f"que las cumple y otro que las viola ({len(gen.sin_caso())} sin caso posible, en conformidad/cobertura.json)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
