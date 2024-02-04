from scrapy import Spider, Request
from xml.etree import ElementTree


class ApplePriceScraperSpider(Spider):
    """
    Scrapy spider to scrape the prices of all the available iPhones from https://apple.com
    """

    name = "apple_scraper"
    start_urls = ["https://www.apple.com/shop/sitemaps/sitemap-buy.xml"]
    custom_settings = {"LOG_LEVEL": "INFO"}

    def __init__(self):
        self.brand = "Apple"
        self.desired_url_path_len = 7
        self.iphone_url_path = "https://www.apple.com/shop/buy-iphone"
        self.headers = {
            "authority": "www.apple.com",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "en-US",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "upgrade-insecure-requests": "1",
        }
        self.cookies = {
            "geo": "US",
        }

    def text_to_xml(self, response_text) -> ElementTree.Element | None:
        try:
            xml_data = ElementTree.fromstring(response_text)
            return xml_data
        except (TypeError, ElementTree.ParseError) as ex:
            self.logger.error("XML parse error: %s", str(ex))
            return None

    def get_sitemap_product_urls(self, xml) -> list:
        iphone_urls = []

        def is_iphone_page(url) -> bool | None:
            """
            Checks that the URL belongs to an iPhone page
            and is a specific model that can be bought.
            - https://www.apple.com/shop/buy-iphone (iPhone page)
            - https://www.apple.com/shop/buy-iphone/iphone-13/6.1-inch-display-128gb-starlight-unlocked (Specific model)
            """
            url_path_len = len(url.split("/")) >= self.desired_url_path_len
            if url.startswith(self.iphone_url_path) and url_path_len:
                return True

        try:
            iphone_urls = [node[0].text for node in xml if is_iphone_page(node[0].text)]
        except Exception as ex:
            # Always useful to catch exceptions in case the data format changes
            self.logger.error("XML scrape error: %s", str(ex))
        return iphone_urls

    def parse_product_page(self, response):
        # TODO
        yield {"product_url": response.url}

    def parse(self, response):
        xml = self.text_to_xml(response.text)
        if xml:
            url_list = self.get_sitemap_product_urls(xml)
            for url in url_list:
                yield Request(
                    url,
                    headers=self.headers,
                    cookies=self.cookies,
                    callback=self.parse_product_page,
                )
        else:
            self.logger.warning("XML sitemap data not found")
            return None
