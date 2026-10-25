# Análisis de Comparativa de Proveedores (LLMs)

## 1. Puntuación de calidad
Tras evaluar las 15 respuestas generadas por los tres modelos locales, estas son las puntuaciones de calidad (del 1 al 5) asignadas a cada una:

*   **Correo 1 (Entregas sábados):** phi3 (4), llama3.2 (4), qwen3 (4)
*   **Correo 2 (Cafetera gotea):** phi3 (4), llama3.2 (3), qwen3 (1)
*   **Correo 3 (15 kg blend):** phi3 (4), llama3.2 (5), qwen3 (3)
*   **Correo 4 (Factura septiembre):** phi3 (4), llama3.2 (5), qwen3 (2)
*   **Correo 5 (Hotel nuevo):** phi3 (5), llama3.2 (5), qwen3 (1)

**Promedios de calidad resultantes:**
1.  **Llama 3.2:** 4.4 / 5
2.  **Phi-3:** 4.2 / 5
3.  **Qwen 3 (0.6b):** 2.2 / 5

---

## 2. Análisis del consumo de tokens
En la tabla de resultados se observa una anomalía muy clara con el modelo **qwen3**. Para respuestas extremadamente cortas (a veces de una sola línea), registra un consumo altísimo en `tokens_salida` (entre 87 y 162), mientras que la columna `tokens_entrada` registra siempre el valor de `1`.

**Explicación:**
Esto no se debe a que el modelo consuma más por escribir lo mismo, sino a un error en cómo la API (en este caso Ollama con el formato `messages`) está devolviendo los metadatos de uso (`usage`). Lo que probablemente está ocurriendo es que la API está devolviendo el total de tokens combinados en el campo de salida, y dejando por defecto un `1` en el campo de entrada, provocando que nuestro script asigne mal los valores en el CSV.

---

## 3. Elección de modelo para 2.000 correos al mes
Basándome en los datos reales extraídos de la tabla de pruebas (coste, latencia y calidad), el modelo elegido para contestar 2.000 correos mensuales es **Llama 3.2**.

**Justificación con datos:**
*   **Calidad:** Es el modelo con la mejor puntuación promedio (4.4 sobre 5), superando a Phi-3 (4.2) y superando ampliamente a Qwen 3 (2.2). Sus respuestas son las más profesionales y completas.
*   **Coste:** Al utilizar modelos de ejecución local mediante Ollama, el coste de la API es de 0.00 USD en todos los casos, por lo que responder 2.000 o 20.000 correos será gratuito a nivel de proveedor.
*   **Latencia:**