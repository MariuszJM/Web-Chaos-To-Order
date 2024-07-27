from src.processors.processor_factory import ProcessorFactory


def process_platforms(platforms, queries, sources_per_query, specific_questions, time_horizon, max_outputs):
    for index, platform in enumerate(platforms):
        try:
            processor = ProcessorFactory.create_processor(platform)
            top_results, results_without_content, less_relevant_results, rejected_results = processor.process(
                queries, 
                sources_per_query=sources_per_query, 
                questions=specific_questions, 
                time_horizon=time_horizon, 
                max_outputs_per_platform=max_outputs
            )
            if index > 0:
                combined_results.combine(top_results)
                combined_no_content_results.combine(results_without_content)
                combined_less_relevant_results.combine(less_relevant_results)
                combined_rejected_results.combine(rejected_results)
            else:
                combined_results = top_results
                combined_no_content_results = results_without_content
                combined_less_relevant_results = less_relevant_results
                combined_rejected_results = rejected_results
                run_name = processor.provide_run_name(queries, specific_questions)

        except ValueError as e:
            print(e)

    return combined_results, combined_no_content_results, combined_less_relevant_results, combined_rejected_results, run_name
