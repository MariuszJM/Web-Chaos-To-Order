from abc import ABC, abstractmethod
from typing import List
from src.data_storage import DataStorage
from src.llm.llm_factory import LLMFactory

MODEL_PLATFORM = "ollama"
MODEL_NAME = "llama3:instruct"


class BaseProcessor(ABC):
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.llm = LLMFactory.create_llm(model_type=MODEL_PLATFORM, model_name=MODEL_NAME)

    def process(self, queries: List[str], sources_per_query: int, questions: List[str], time_horizon, max_outputs_per_platform=7) -> DataStorage:
        combined_data = self.combine_multiple_queries(queries, sources_per_query, time_horizon)
        data_with_content, data_without_content = self.check_source_content(combined_data)
        tagged_data = self.add_smart_tags(data_with_content, questions)
        relevant_data, not_relevant_data = self.filter_relevant_sources(tagged_data)
        ranked_data = self.rank_sources_by_relevance(relevant_data)
        top_data, less_relevant_data = self.choose_top_sources(ranked_data, max_outputs_per_platform)
        return top_data, data_without_content, less_relevant_data, not_relevant_data
    
    def combine_multiple_queries(self, queries: List[str], sources_per_query: int, time_horizon) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_list = self.process_query(query, sources_per_query, time_horizon)
            combined_storage.add_data_list(self.platform_name, query_list)
        return combined_storage
    
    @abstractmethod
    def process_query(self, query: str, num_top_sources: int, time_horizon) -> DataStorage:
        pass

    def add_smart_tags(self, data_storage: DataStorage, questions: List[str]) -> DataStorage:
        for platform_name in data_storage.data.keys():
            for title in data_storage.data[platform_name].keys():
                content = data_storage.data[platform_name][title].get("content")
                if not content:
                    continue

                summary, combine_flag = self.llm.summarize(content=content, questions=questions)

                if combine_flag:
                    combined_summary = self.llm.organize_summarization_into_one(summary)
                    data_storage.data[platform_name][title].pop("content")
                    data_storage.data[platform_name][title]["detailed_summary"] = summary
                    data_storage.data[platform_name][title]["summary"] = combined_summary
                else:
                    data_storage.data[platform_name][title]["summary"] = summary

                relevance_score = 0
                for question in questions:
                    answer = self.llm.ask_llama_question(question, content, summary)
                    if self.llm.validate_with_q_and_a_relevance(question, answer) and self.llm.validate_with_llm_knowledge(question, answer):
                        if "Q&A" not in data_storage.data[platform_name][title]:
                            data_storage.data[platform_name][title]["Q&A"] = {}
                        data_storage.data[platform_name][title]["Q&A"][question] = answer
                        relevance_score += 1
                
                data_storage.data[platform_name][title]["relevance_score"] = relevance_score
        return data_storage

    def filter_relevant_sources(self, data_storage: DataStorage) -> DataStorage:
        relevant_data = DataStorage()
        not_relevant_data = DataStorage()
        for platform_name, titles in data_storage.data.items():
            for title, info in titles.items():
                if info.get("relevance_score", 0) > 0:
                    relevant_data.add_data(platform_name, title, **titles[title])
                else:
                    not_relevant_data.add_data(platform_name, title, **titles[title])
        return relevant_data, not_relevant_data

    def rank_sources_by_relevance(self, data_storage: DataStorage) -> DataStorage:
        sorted_data = {}
        for platform_name, titles in data_storage.data.items():
            sorted_titles = dict(sorted(titles.items(), key=lambda item: item[1].get("relevance_score", 0), reverse=True))
            for title in sorted_titles:
                sorted_titles[title].pop("relevance_score", None)
            sorted_data[platform_name] = sorted_titles
        data_storage.data = sorted_data
        return data_storage
    
    def choose_top_sources(self, data_storage: DataStorage, max_outputs_per_platform: int):
        top_data = DataStorage()
        less_relevant_data = DataStorage()
        for platform_name, titles in data_storage.data.items():
            for title in titles.keys():
                if len(top_data.data.get(platform_name, {})) < max_outputs_per_platform:
                    top_data.add_data(platform_name, title, **titles[title])
                else:
                    less_relevant_data.add_data(platform_name, title, **titles[title])
        return top_data, less_relevant_data

    def check_source_content(self, data_storage: DataStorage):
        data_with_content = DataStorage()
        data_without_content = DataStorage()
        for platform_name, titles in data_storage.data.items():
            for title, details in titles.items():
                content = details.get("content")
                if content:
                    data_with_content.add_data(platform_name, title, **titles[title])
                else:
                    data_without_content.add_data(platform_name, title, **titles[title])
        return data_with_content, data_without_content


class InDepthProcessor(BaseProcessor):
    def process_query(self, query: str, num_top_sources: int, time_horizon) -> DataStorage:
        sources = self.fetch_source_items(query, 2 * num_top_sources)
        filtered_sources = self.filter_low_quality_sources(sources, time_horizon)
        top_sources = self.select_top_sources(filtered_sources, num_top_sources)
        data_storage = self.collect_source_details(top_sources)
        return data_storage
    
    @abstractmethod
    def fetch_source_items(self, query: str, limit: int) -> List[dict]:
        pass
    
    @abstractmethod
    def filter_low_quality_sources(self, sources: List[dict], time_horizon) -> List[dict]:
        pass
    
    def select_top_sources(self, sources: List[dict], num_top_sources: int) -> List[dict]:
        return sources[:num_top_sources]
    
    @abstractmethod
    def collect_source_details(self, sources: List[dict]) -> DataStorage:
        pass

    @abstractmethod
    def fetch_detailed_content(self, identifier: str) -> str:
        pass
