import pytest
from src.llm.base_llm import BaseLLM

class MockLLM(BaseLLM):
    def generate_response(self, prompt: str) -> str:
        return "Mock response"

@pytest.fixture
def mock_llm():
    return MockLLM("mock_model")

def test_split_text_to_chunks(mock_llm):
    text = "This is a test text " * 500  # Long text to ensure chunking
    chunks = mock_llm.split_text_to_chunks(text, chunk_size=1000, chunk_overlap=100)
    assert len(chunks) > 1

def test_summarize(mock_llm):
    content = "This is some content that needs to be summarized."
    summary, combine_flag = mock_llm.summarize(content)
    assert isinstance(summary, str)
    assert not combine_flag

def test_organize_summarization_into_one(mock_llm):
    combined_text = "Summary part one. Summary part two."
    organized_summary = mock_llm.organize_summarization_into_one(combined_text)
    assert isinstance(organized_summary, str)

def test_ask_llama_question(mock_llm):
    question = "What is the content about?"
    details = "This is detailed content."
    answer = mock_llm.ask_llama_question(question, details, details)
    assert isinstance(answer, str)

def test_validate_with_q_and_a_relevance(mock_llm):
    question = "Is this relevant?"
    answer = "Yes, it is."
    result = mock_llm.validate_with_q_and_a_relevance(question, answer)
    assert result is True or result is False

def test_validate_with_llm_knowledge(mock_llm):
    question = "Is this correct?"
    answer = "Yes, it is correct."
    result = mock_llm.validate_with_llm_knowledge(question, answer)
    assert result is True or result is False

def test_provide_run_name(mock_llm):
    queries = ["query1", "query2"]
    questions = ["question1", "question2"]
    run_name = mock_llm.provide_run_name(queries, questions)
    assert isinstance(run_name, str)
    assert len(run_name) <= 24
