class BaseScrapper:
    def fetch_website_content(self, url):
        raise NotImplementedError("This method should be overridden by subclasses")
