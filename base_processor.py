from abc import ABC, abstractmethod
from typing import List
from data_storage import DataStorage


class SourceProcessor(ABC):

    def combine_multiple_queries(
        self, queries: List[str], num_sources_per_query: int, questions: List[str]
    ) -> DataStorage:
        combined_storage = DataStorage()
        for query in queries:
            query_storage = self.process_query(query, num_sources_per_query)
            combined_storage.combine(query_storage)
        combined_storage = self.add_summary_info(combined_storage, questions)
        return combined_storage
    @abstractmethod
    def process_query(self, query: str, num_top_sources: int) -> DataStorage:
        pass
