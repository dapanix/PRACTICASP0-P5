"""Sesión 1. Comparativa de proveedores sobre los mismos correos (genera comparativa.csv)."""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "P3"))  # llm_client.py vive en P3
from llm_client import FORMATOS, LLM, MODELOS  # noqa: E402

# Adaptación a Ollama: los "proveedores" son los tres modelos locales, cada uno con un formato
# de API distinto (chat, responses, messages), como en el __main__ de llm_client.py
PROVEEDORES = list(zip(MODELOS, FORMATOS))

SISTEMA = ("Eres el asistente de atención al cliente de Tostadero Retiro S.L. "
           "Responde en español y en dos frases como máximo.")
CORREOS = [
    "¿Hacéis entregas los sábados en Chamberí?",
    "La cafetera gotea por el grupo 1 desde esta mañana.",
    "Quiero 15 kg de blend y dos cajas de vasos para el jueves.",
    "¿Por qué la factura de septiembre es más alta que la de agosto?",
    "Somos un hotel nuevo en Centro: ¿qué café nos recomendáis para el desayuno?",
]

with open("comparativa.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["proveedor", "correo", "segundos", "tokens_entrada", "tokens_salida",
                "coste_usd", "calidad_1a5", "respuesta"])
    for modelo, formato in PROVEEDORES:
        llm = LLM(modelo, formato)
        for correo in CORREOS:
            r = llm.responder(SISTEMA, correo)
            w.writerow([f"{modelo} ({formato})", correo, f"{r.segundos:.2f}", r.tokens_entrada,
                        r.tokens_salida, r.coste_usd, "", r.texto])
            print(f"{modelo:16} {formato:9} {r.segundos:5.2f} s  {r.tokens_entrada}/{r.tokens_salida}  "
                  f"{correo[:40]}")

print("Hecho: abre comparativa.csv y puntúa la columna calidad_1a5 en equipo.")
