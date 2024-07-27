from src.llm.ollama_llm import OllamaLLM


class LLMFactory:
    @staticmethod
    def create_llm(model_type: str, model_name: str = "llama3:instruct"):
        if model_type == "ollama":
            return OllamaLLM(model_name=model_name)
        else:
            raise ValueError(f"Unsupported model type: {model_type}")
