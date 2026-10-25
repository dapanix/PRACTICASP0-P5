"""Sesión 1. El mismo encargo a tres modelos locales de Ollama: respuesta, tokens y latencia."""
import re
import time

import openai

# Ollama expone una API compatible con Chat Completions de OpenAI en este puerto
OLLAMA = "http://localhost:11434/v1"
MODELOS = ["phi3:latest", "llama3.2:latest", "qwen3:0.6b"]
SISTEMA = ("Eres el asistente de atención al cliente de Tostadero Retiro S.L. "
           "Responde en español y en dos frases como máximo.")
CORREO = ("Hola, soy Marta del Bar La Esquina. La cafetera vuelve a perder presión y mañana "
          "tenemos el pedido 1004 pendiente. ¿Me decís algo? Gracias")
PETICION = ("Clasifica este correo como pedido, incidencia, consulta o mixto y redacta "
            f"una respuesta breve:\n\n{CORREO}")


def con_ollama(modelo: str) -> tuple[str, int, int]:
    cliente = openai.OpenAI(base_url=OLLAMA, api_key="ollama")  # la clave se exige pero se ignora
    r = cliente.chat.completions.create(
        model=modelo,
        messages=[{"role": "system", "content": SISTEMA}, {"role": "user", "content": PETICION}],
    )
    texto = r.choices[0].message.content or ""
    # qwen3 es un modelo de razonamiento: quitamos su bloque <think>...</think>
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()
    return texto, r.usage.prompt_tokens, r.usage.completion_tokens


if __name__ == "__main__":
    for modelo in MODELOS:
        inicio = time.perf_counter()
        texto, t_in, t_out = con_ollama(modelo)
        print(f"\n=== {modelo} | {time.perf_counter() - inicio:.2f} s | "
              f"{t_in} tokens entrada | {t_out} tokens salida\n{texto}")
