from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Tuple


class BaseLLM:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def split_text_to_chunks(self, text: str, chunk_size=7500, chunk_overlap=150) -> List[str]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(text)

    def generate_response(self, prompt: str) -> str:
        raise NotImplementedError("Subclasses should implement this method.")

    def summarize(self, content: str, chunk_size=7500, questions=[]) -> Tuple[str, bool]:
        if not content:
            return "Content not available.", False

        chunks = self.split_text_to_chunks(content, chunk_size=chunk_size)
        summaries = []
        prompt_base = (f"You are an expert content summarizer. Summarize the content based on the following text into concise paragraphs. "
                       f"Each paragraph should be separated by a newline and focus on a single key point. Don't add any comments, just the summary. "
                       f"Prioritize the information which can help answer the questions: {questions}:")
        
        for chunk in chunks:
            prompt = prompt_base + chunk
            summary = self.generate_response(prompt)
            summaries.append(summary)

        combined_summary = "\n".join(summaries)
        
        if len(self.tokenize(combined_summary)) > 7500:
            combined_summary, _ = self.summarize(combined_summary, chunk_size=7500)
        
        return combined_summary, len(summaries) > 1

    def tokenize(self, text: str) -> List[str]:
        return text.split()

    def organize_summarization_into_one(self, combined_text: str) -> str:
        prompt = (f"You are an expert content information organizer. Combine and organize the following summaries into a single cohesive summary. "
                  "Each paragraph should be separated by a newline and focus on a single key point. Don't add any comments, just the summary. "
                  "Remove redundant information. Make it as detailed as possible. The output shouldn't be much smaller than the input. "
                  "You are not a summarizer, just an organizer.\nSummaries: {combined_text}")
        return self.generate_response(prompt)

    def ask_llama_question(self, question: str, details: str, detailed_summary: str) -> str:
        text = details if len(self.tokenize(details)) <= 7500 else detailed_summary
        prompt = f"Based on the text, answer the question: {question}\n\ntext:\n{text}"
        return self.generate_response(prompt)

    def validate_with_q_and_a_relevance(self, question: str, answer: str) -> bool:
        prompt = (f"Given the answer: \"{answer}\", does it provide a precise and specific response to the question: \"{question}\" without introducing unrelated details, "
                  "general tips, or inferred information not explicitly stated in the text? Please provide a 'yes' or 'no' response.")
        response = self.generate_response(prompt)
        return 'yes' in response.lower()

    def validate_with_llm_knowledge(self, question: str, answer: str) -> bool:
        prompt = (f"Given the answer: \"{answer}\" for the question: \"{question}\", based on your knowledge, is this answer truthful? Please provide a 'yes' or 'no' response.")
        response = self.generate_response(prompt)
        return not 'no' in response.lower()

    def provide_run_name(self, queries: List[str], questions: List[str]) -> str:
        prompt = (f"Create a short name (up to 24 characters) based on the following queries and questions, provide only the answer without any additional text:\n\n"
                  f"Queries:\n{', '.join(queries)}\n\nQuestions:\n{', '.join(questions)}\n"
                  "Aim is to provide a short name to as precisely as possible describe the search, which makes the best sense.")
        response = self.generate_response(prompt)
        return response.replace(" ", "_")
