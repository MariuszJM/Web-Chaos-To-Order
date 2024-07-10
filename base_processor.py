from abc import ABC, abstractmethod
from typing import List
from data_storage import DataStorage
from LLMProcessor import LLMProcessor


class SourceProcessor(ABC):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.llm_processor = LLMProcessor()

    def combine_multiple_queries(
        self, queries: List[str], num_sources_per_query: int, questions: List[str]
    ) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_storage = self.process_query(query, num_sources_per_query)
            combined_storage.combine(query_storage)
        combined_storage = self.add_smart_tags(combined_storage, questions)
        return combined_storage
    
    def process_query(self, query: str, num_top_sources: int) -> DataStorage:
        sources = self.fetch_source_items(query, 2 * num_top_sources)
        filtered_sources = self.filter_low_quality_sources(sources)
        top_sources = self.select_top_sources(filtered_sources, num_top_sources)
        return top_sources
    
    @abstractmethod
    def fetch_detailed_content(self, identifier: str) -> str:
        pass

    @abstractmethod
    def fetch_source_items(self, query: str, limit: int) -> List[dict]:
        pass

    @abstractmethod
    def filter_low_quality_sources(self, sources: List[dict]) -> List[dict]:
        pass

    @abstractmethod
    def select_top_sources(self, sources: List[dict], num_top_sources: int) -> DataStorage:
        pass

    def add_smart_tags(self, data_storage: DataStorage, questions: List[str]) -> DataStorage:
        for source in data_storage.data.keys():
            for title in data_storage.data[source].keys():
                content = data_storage.data[source][title].get("details")
                if not content:
                    continue
                
                # If content is a dict, convert it to a string representation
                if isinstance(content, dict):
                    content = "\n".join([f"{chapter}: {', '.join(lectures)}" for chapter, lectures in content.items()])

                summary, combine_flag = self.llm_processor.summarize(content)

                if combine_flag:
                    combined_summary = self.llm_processor.organize_summarization_into_one(summary)
                    data_storage.data[source][title]["detailed_summary"] = summary
                    data_storage.data[source][title]["summary"] = combined_summary
                else:
                    data_storage.data[source][title]["summary"] = summary

                for question in questions:
                    answer = self.llm_processor.ask_llama_question(question, content, summary)
                    if self.llm_processor.score_q_and_a_relevance(question, answer):
                        if "Q&A" not in data_storage.data[source][title]:
                            data_storage.data[source][title]["Q&A"] = {}
                        data_storage.data[source][title]["Q&A"][question] = answer
        return data_storage
