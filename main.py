import os
import yaml
from src.data_storage import DataStorage
from src.llm import LLM
from src.utils import load_config, create_output_directory
from src.processors.processor_factory import ProcessorFactory

if __name__ == "__main__":
    execution_config = load_config('./config/execution_config.yaml')
    sources_per_query = execution_config['sources_per_query']
    user_config = load_config('./config/user_config.yaml')
    queries = user_config['search_phrases']
    platforms = [platform.lower() for platform in user_config['platforms']]
    max_outputs_per_platform = user_config['max_outputs_per_platform']
    time_horizon = user_config['time_horizon']
    specific_questions = user_config['specific_questions']

    llm = LLM()
    name = llm.provide_run_name(queries, specific_questions)
    combined_data = DataStorage()
    comb_data_witout_content = DataStorage()
    comb_less_relevant_data = DataStorage()
    comb_rejected_by_relevance = DataStorage()

    for platform_name in platforms:
        try:
            processor = ProcessorFactory.create_processor(platform_name)
            top_data, data_witout_content, less_relevant_data, rejected_by_relevance = processor.process(
                queries, 
                sources_per_query=sources_per_query, 
                questions=specific_questions, 
                time_horizon=time_horizon, 
                max_outputs_per_platform=max_outputs_per_platform
            )
            combined_data.combine(top_data)
            comb_data_witout_content.combine(data_witout_content)
            comb_less_relevant_data.combine(less_relevant_data)
            comb_rejected_by_relevance.combine(rejected_by_relevance)
        except ValueError as e:
            print(e)

    output_dir = create_output_directory('runs')
    combined_data.save_to_yaml(os.path.join(output_dir, f"{name}.yaml"))
    filtered = {
        'data_witout_content': comb_data_witout_content.data,
        'less_relevant_data': comb_less_relevant_data.data,
        'rejected_by_relevance': comb_rejected_by_relevance.data
    }
    with open(os.path.join(output_dir, f"filtered_data.yaml"), "w") as file:
        yaml.dump(filtered, file, default_flow_style=False, sort_keys=False)
    
    with open(os.path.join(output_dir, f"run_config.yaml"), "w") as file:
        yaml.dump(user_config, file, default_flow_style=False, sort_keys=False)
    
    print("Combined Data:", combined_data.to_dict())
    print(f"Data saved to: {output_dir}")
