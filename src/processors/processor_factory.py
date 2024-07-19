from src.processors.github_processor import GitHubProcessor
from src.processors.udemy_processor import UdemyProcessor
from src.processors.youtube_processor import YouTubeProcessor
from src.processors.google_processor import GoogleProcessor

class ProcessorFactory:
    @staticmethod
    def create_processor(platform_with_scope):
        platform_parts = platform_with_scope.split(':')
        platform = platform_parts[0].lower()
        
        processors = {
            'youtube': YouTubeProcessor,
            'github': GitHubProcessor,
            'udemy': UdemyProcessor,
            'google': GoogleProcessor
        }
        
        if platform not in processors:
            raise ValueError(f"Platform: {platform} is not available")
        
        processor_class = processors[platform]
        return processor_class(platform_with_scope)
