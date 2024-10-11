import ollama
from src.llm.base_llm import BaseLLM


class OllamaLLM(BaseLLM):
    def __init__(self, model_name="llama3.1:8b-instruct-q4_0"):
        super().__init__(model_name)

    def generate_response(self, prompt: str) -> str:
        response = ollama.generate(model=self.model_name, prompt=prompt)
        return response.get('response', "").strip()
