import ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter

class LLMProcessor:
    def __init__(self):
        pass

    def split_text_to_chunks(self, text, chunk_size=7500, chunk_overlap=150):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        return text_splitter.split_text(text)

    def summarize_transcript(self, transcript, chunk_size=7500):
        if not transcript:
            return "Transcript not available."
        chunks = self.split_text_to_chunks(transcript, chunk_size=chunk_size)
        questions = 'What is the best habit to follow every day?'
        Summary_format = """**Overview**


      overwiew content...


      **first summary point name**


      First summary point content...
      
      **second summary point name**


      Second summary point content...
      
      etc...

"""
        summaries = []
        for chunk in chunks:
            prompt = (f"""You are an expert content summarizer. Summarize the video based on the following transcript. 
                      Focus on essential information and answer the following questions: {questions}
                      Use bullet points and separate each point with a newline and the following output format: {Summary_format}.
                      Transcript: {chunk}""")
            response = ollama.generate(model="llama3:instruct", prompt=prompt)
            summary = response.get('response', "").strip()
            summaries.append(summary)
        
        combine_flag = False
        if len(summaries) > 1:
            combine_flag = True

        combined_summary = "\n".join(summaries)
        if len(self.tokenize(combined_summary)) > 7500:
            combined_summary, _ = self.summarize_transcript(combined_summary, chunk_size=7500)
        
        return combined_summary, combine_flag

    def tokenize(self, text):
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

        response = ollama.generate(model="llama3:instruct", prompt=prompt)
        organized_summary = response.get('response', "").strip()
        return organized_summary

    def ask_llama_question(self, question: str, details: str, detailed_summary: str) -> str:
        text = details if len(self.tokenize(details)) <= 7500 else detailed_summary
        prompt = f"""
        Based on the text, answer the question: {question}
        
        text:
        {text}
        """
        response = ollama.generate(model="llama3:instruct", prompt=prompt)
        answer = response.get('response', "").strip()
        return answer
