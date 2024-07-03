from abc import ABC, abstractmethod
from typing import List
from data_storage import DataStorage


class SourceProcessor(ABC):

    @abstractmethod
    def combine_multiple_queries(
        self, queries: List[str], num_sources_per_query: int
    ) -> DataStorage:
        pass
    @abstractmethod
    def process_query(self, query: str, num_top_sources: int) -> DataStorage:
        pass
