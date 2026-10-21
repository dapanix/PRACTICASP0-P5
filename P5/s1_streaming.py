"""Sesión 1. Streaming: mostrar la respuesta según se genera (mejora la latencia percibida)."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "P3"))  # llm_client.py vive en P3
from llm_client import FORMATOS, LLM  # noqa: E402

PREGUNTA = "Explica en cinco líneas qué es un acuerdo de nivel de servicio (SLA)."

# Adaptación a Ollama: un mismo modelo servido por los tres formatos de API
for formato in FORMATOS:
    print(f"--- llama3.2 ({formato})")
    inicio = time.perf_counter()
    primero = None
    for trozo in LLM("llama3.2:latest", formato).responder_stream("Responde en español.", PREGUNTA):
        if primero is None:
            primero = time.perf_counter() - inicio
        print(trozo, end="", flush=True)
    print(f"\n[primer fragmento: {primero:.2f} s | total: {time.perf_counter() - inicio:.2f} s]\n")
