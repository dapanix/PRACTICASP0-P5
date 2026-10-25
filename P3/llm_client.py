"""Sesión 1. Una interfaz común para varios formatos de API (patrón Adapter), todo con Ollama.

Ollama habla tres formatos de API en el mismo puerto: Chat Completions (/v1/chat/completions),
Responses (/v1/responses) y Messages de Anthropic (/v1/messages). Cada uno se usa con su SDK
oficial (openai o anthropic) apuntando a Ollama.

El resto del bloque usará LLM.responder() cuando el formato dé igual."""
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass

import anthropic
import openai

OLLAMA = "http://localhost:11434"
MODELOS = ["phi3:latest", "llama3.2:latest", "qwen3:0.6b"]
FORMATOS = ["chat", "responses", "messages"]

# Precios en USD por millón de tokens (entrada, salida). Los modelos locales no cobran por token,
# así que valen 0. Si quieres un coste de referencia, pon aquí el de un modelo de nube equivalente.
PRECIOS: dict[str, tuple[float, float]] = {
    "phi3:latest": (0.0, 0.0),
    "llama3.2:latest": (0.0, 0.0),
    "qwen3:0.6b": (0.0, 0.0),
}

MAX_TOKENS_POR_DEFECTO = 1024  # Messages exige max_tokens; en el resto solo se envía si se pasa


def _limpiar(texto: str) -> str:
    """qwen3 es un modelo de razonamiento: quitamos su bloque <think>...</think>, incluso
    si se cortó por max_tokens antes de cerrarse (entonces no queda texto)."""
    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL)
    return re.sub(r"<think>.*", "", texto, flags=re.DOTALL).strip()


@dataclass
class Respuesta:
    texto: str
    tokens_entrada: int
    tokens_salida: int
    segundos: float
    modelo: str

    @property
    def coste_usd(self) -> float | None:
        if self.modelo not in PRECIOS:
            return None
        p_in, p_out = PRECIOS[self.modelo]
        return (self.tokens_entrada * p_in + self.tokens_salida * p_out) / 1_000_000


class LLM:
    """modelo: uno de MODELOS (por defecto llama3.2). formato: 'chat' | 'responses' | 'messages'.

    Cada formato usa su SDK: Chat Completions y Responses con openai, Messages con anthropic."""

    def __init__(self, modelo: str = "llama3.2:latest", formato: str = "chat"):
        if formato not in FORMATOS:
            raise ValueError(f"formato debe ser uno de {FORMATOS}")
        self.modelo = modelo
        self.formato = formato
        if formato == "messages":
            self._c = anthropic.Anthropic(base_url=OLLAMA, api_key="ollama", max_retries=3)
        else:  # la clave se exige pero se ignora
            self._c = openai.OpenAI(base_url=OLLAMA + "/v1", api_key="ollama", max_retries=3)

    def responder(self, sistema: str, prompt: str, temperatura: float | None = None,
                  max_tokens: int | None = None) -> Respuesta:
        t0 = time.perf_counter()
        if self.formato == "responses":
            extra = {}
            if temperatura is not None:
                extra["temperature"] = temperatura
            if max_tokens is not None:
                extra["max_output_tokens"] = max_tokens
            r = self._c.responses.create(
                model=self.modelo, instructions=sistema, input=prompt, **extra)
            texto, t_in, t_out = r.output_text, r.usage.input_tokens, r.usage.output_tokens
        elif self.formato == "messages":
            extra = {} if temperatura is None else {"temperature": temperatura}
            r = self._c.messages.create(
                model=self.modelo,
                system=sistema,  # el mensaje de sistema no va dentro de messages
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or MAX_TOKENS_POR_DEFECTO,  # obligatorio
                **extra,
            )
            # el texto llega repartido en bloques (text, thinking...): unimos los de tipo text
            texto = "".join(b.text for b in r.content if b.type == "text")
            t_in, t_out = r.usage.input_tokens, r.usage.output_tokens
        else:  # "chat"
            extra = {}
            if temperatura is not None:
                extra["temperature"] = temperatura
            if max_tokens is not None:
                extra["max_tokens"] = max_tokens
            r = self._c.chat.completions.create(
                model=self.modelo,
                messages=[{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
                **extra,
            )
            texto = r.choices[0].message.content or ""
            t_in, t_out = r.usage.prompt_tokens, r.usage.completion_tokens
        return Respuesta(_limpiar(texto or ""), t_in, t_out, time.perf_counter() - t0, self.modelo)

    def responder_stream(self, sistema: str, prompt: str, temperatura: float | None = None,
                         max_tokens: int | None = None) -> Iterator[str]:
        """Reto opcional: generador de fragmentos de texto (sin filtrar <think> de qwen3)."""
        if self.formato == "responses":
            extra = {}
            if temperatura is not None:
                extra["temperature"] = temperatura
            if max_tokens is not None:
                extra["max_output_tokens"] = max_tokens
            flujo = self._c.responses.create(
                model=self.modelo, instructions=sistema, input=prompt, stream=True, **extra)
            for ev in flujo:
                if ev.type == "response.output_text.delta":
                    yield ev.delta
        elif self.formato == "messages":
            extra = {} if temperatura is None else {"temperature": temperatura}
            with self._c.messages.stream(
                model=self.modelo, system=sistema,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens or MAX_TOKENS_POR_DEFECTO, **extra,
            ) as flujo:
                yield from flujo.text_stream
        else:  # "chat"
            extra = {}
            if temperatura is not None:
                extra["temperature"] = temperatura
            if max_tokens is not None:
                extra["max_tokens"] = max_tokens
            flujo = self._c.chat.completions.create(
                model=self.modelo, stream=True,
                messages=[{"role": "system", "content": sistema}, {"role": "user", "content": prompt}],
                **extra,
            )
            for trozo in flujo:
                if trozo.choices and trozo.choices[0].delta.content:
                    yield trozo.choices[0].delta.content


if __name__ == "__main__":
    # un formato distinto por modelo, para ejercitar las tres ramas
    for modelo, formato in zip(MODELOS, FORMATOS):
        r = LLM(modelo, formato).responder("Responde en una frase.", "¿Qué es un token?")
        print(f"{modelo:16} {formato:9} {r.segundos:5.2f} s  {r.tokens_entrada:4}/{r.tokens_salida:<4} "
              f"{r.coste_usd}  {r.texto}")
