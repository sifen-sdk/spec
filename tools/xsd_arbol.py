#!/usr/bin/env python3
"""Genera xsd/arbol.json: un volcado neutral de los esquemas de xsd/oficial.

Por cada archivo lista sus tipos complejos (con sus elementos hijos, tipo y ocurrencia), sus tipos simples (base y
restricciones) y sus elementos globales. No interpreta ni corrige nada: es lo que dicen los esquemas.

Uso:  python3 tools/xsd_arbol.py            escribe xsd/arbol.json
      python3 tools/xsd_arbol.py --check    falla si xsd/arbol.json no está al día
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

XS = "{http://www.w3.org/2001/XMLSchema}"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFICIAL = os.path.join(RAIZ, "xsd", "oficial")
SALIDA = os.path.join(RAIZ, "xsd", "arbol.json")


def ocurrencia(e):
    return {"min": e.get("minOccurs", "1"), "max": e.get("maxOccurs", "1")}


def restricciones(simple):
    r = simple.find(XS + "restriction")
    if r is None:
        return {}
    out = {"base": r.get("base")}
    enum = []
    for f in r:
        nombre = f.tag.replace(XS, "")
        if nombre == "enumeration":
            enum.append(f.get("value"))
        elif nombre == "pattern":
            out.setdefault("pattern", []).append(f.get("value"))
        elif f.get("value") is not None:
            out[nombre] = f.get("value")
    if enum:
        out["enumeration"] = enum
    return out


def hijos(nodo):
    """Elementos hijos de un tipo complejo, en orden, bajando por sequence/choice/all."""
    out = []
    for c in nodo:
        tag = c.tag.replace(XS, "")
        if tag == "element":
            item = {"nombre": c.get("name") or c.get("ref"), "tipo": c.get("type"), **ocurrencia(c)}
            inline_c = c.find(XS + "complexType")
            inline_s = c.find(XS + "simpleType")
            if inline_c is not None:
                item["hijos"] = hijos(inline_c)
            if inline_s is not None:
                item["restricciones"] = restricciones(inline_s)
            out.append(item)
        elif tag in ("sequence", "choice", "all"):
            sub = hijos(c)
            if tag == "choice":
                for s in sub:
                    s["en_choice"] = True
            if c.get("minOccurs") == "0":
                for s in sub:
                    s["contenedor_opcional"] = True
            out.extend(sub)
        elif tag in ("complexContent", "extension"):
            out.extend(hijos(c))
    return out


def atributos(nodo):
    return [
        {"nombre": a.get("name"), "tipo": a.get("type"), "uso": a.get("use", "optional")}
        for a in nodo.iter(XS + "attribute")
    ]


def volcar(ruta):
    raiz = ET.parse(ruta).getroot()
    data = {
        "incluye": [
            (i.get("schemaLocation") or "").split("/")[-1].split(" ")[-1]
            for i in raiz
            if i.tag in (XS + "include", XS + "import")
        ],
        "elementos": [],
        "tipos_complejos": {},
        "tipos_simples": {},
    }
    for n in raiz:
        tag = n.tag.replace(XS, "")
        if tag == "element":
            item = {"nombre": n.get("name"), "tipo": n.get("type")}
            inline = n.find(XS + "complexType")
            if inline is not None:
                item["hijos"] = hijos(inline)
            data["elementos"].append(item)
        elif tag == "complexType":
            entrada = {"hijos": hijos(n)}
            attrs = atributos(n)
            if attrs:
                entrada["atributos"] = attrs
            data["tipos_complejos"][n.get("name")] = entrada
        elif tag == "simpleType":
            data["tipos_simples"][n.get("name")] = restricciones(n)
    return data


def generar():
    arbol = {}
    for f in sorted(os.listdir(OFICIAL)):
        if f.endswith(".xsd"):
            arbol[f] = volcar(os.path.join(OFICIAL, f))
    return json.dumps(arbol, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main():
    texto = generar()
    if "--check" in sys.argv:
        actual = open(SALIDA, encoding="utf-8").read() if os.path.exists(SALIDA) else ""
        if actual != texto:
            print("xsd/arbol.json no está al día: ejecutá python3 tools/xsd_arbol.py")
            return 1
        return 0
    with open(SALIDA, "w", encoding="utf-8") as fh:
        fh.write(texto)
    return 0


if __name__ == "__main__":
    sys.exit(main())
