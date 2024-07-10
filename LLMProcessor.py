import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

class LLMProcessor:
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
            prompt = (
                f"You are an expert content summarizer. Summarize the content based on the following text in up to 10 points with a newline between each point; "
                f"Focus on essential information to understand the content and be able to use it effectively; Don't add any comments, just summary: {chunk}"
            )
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
        prompt = (f"""You are an expert content information organizer. Combine and organize the following summaries into a single cohesive summary. 
                    Remove redundant informations.
                    Make it as detailed as possible. The output shouldn't be much smaller than the input. You are not summarizer just organizer.
                    Use bullet points and the following output format:
                    
                    **Overview**

                    Overview content...

                    **Summary Points**

                    - First summary point content...
                    - Second summary point content...
                    - etc...

                    Summaries: {combined_text}""")

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
    
    def score_q_and_a_relevance(self, question: str, answer: str):
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