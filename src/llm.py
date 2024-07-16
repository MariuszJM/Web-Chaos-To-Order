import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

class LLM:
    def __init__(self, model_name="llama3:instruct"):
        self.model_name = model_name

    def split_text_to_chunks(self, text, chunk_size=7500, chunk_overlap=150):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(text)

    def summarize(self, content: str, chunk_size=7500) -> str:
        if not content:
            return "Content not available."

        chunks = self.split_text_to_chunks(content, chunk_size=chunk_size)
        summaries = []
        
        for chunk in chunks:
            prompt = f"You are an expert content summarizer. Summarize the content based on the following text into concise paragraphs. Each paragraph should be separated by a newline and focus on a single key point. Don't add any comments, just the summary: {chunk}"
            response = ollama.generate(model=self.model_name, prompt=prompt)
            summary = response.get('response', "").strip()
            summaries.append(summary)

        combined_summary = "\n".join(summaries)
        
        if len(self.tokenize(combined_summary)) > 7500:
            combined_summary, _ = self.summarize(combined_summary, chunk_size=7500)
        
        return combined_summary, len(summaries) > 1

    def tokenize(self, text: str) -> List[str]:
        return text.split()

    def organize_summarization_into_one(self, combined_text: str) -> str:
        prompt =f'''You are an expert content information organizer. Combine and organize the following summaries into a single cohesive summary. 
        Each paragraph should be separated by a newline and focus on a single key point. Don't add any comments, just the summary Remove redundant informations. 
        Make it as detailed as possible. The output shouldn't be much smaller than the input. You are not summarizer just organizer.
        Summaries: {combined_text}''' 
        response = ollama.generate(model=self.model_name, prompt=prompt)
        organized_summary = response.get('response', "").strip()
        return organized_summary

    def ask_llama_question(self, question: str, details: str, detailed_summary: str) -> str:
        text = details if len(self.tokenize(details)) <= 7500 else detailed_summary
        prompt = f"""
        Based on the text, answer the question: {question}
        
        text:
        {text}
        """
        response = ollama.generate(model=self.model_name, prompt=prompt)
        answer = response.get('response', "").strip()
        return answer
    
    def validate_with_q_and_a_relevance(self, question: str, answer: str):
        prompt = f"""
        Given the answer: "{answer}", does it provide a precise and specific response to the question: "{question}" without introducing unrelated details, general tips, or inferred information not explicitly stated in the text? 
        Please provide a "yes" or "no" response.
        """
        response = ollama.generate(model=self.model_name, prompt=prompt)
        answer = response.get('response', "").strip()
        return 'yes' in answer.lower()

    def validate_with_llm_knowledge(self, question: str, answer: str):
        prompt = f"""
        Given the answer: "{answer}" for the question: "{question}", based on your knowledge, is this answer truthful? Please provide a "yes" or "no" response.
        """
        response = ollama.generate(model=self.model_name, prompt=prompt)
        answer = response.get('response', "").strip()
        return not 'no' in answer.lower()
    
    def provide_run_name(self, queries, questions):
        prompt = f"""
        Create a short name (up to 24 characters) based on the following queries and questions, provide only the answer without any additional text:
        
        Queries:
        {", ".join(queries)}
        
        Questions:
        {", ".join(questions)}
        Aim is to provide short name to as precisely possible describe the search, which make the best sense  
        """
        response = ollama.generate(model=self.model_name, prompt=prompt)
        answer = response.get('response', "").strip()
        return answer.replace(" ", "_")