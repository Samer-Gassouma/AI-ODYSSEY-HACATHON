from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from typing import Dict, List, Any
import logging
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from nlp_processor import NLPProcessor

class AdvancedScraper:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.setup_selenium()
        
    def setup_selenium(self):
        """Setup Selenium for JavaScript rendering"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)
        
    async def _fetch_graphql_data(self, endpoint: str, query: str) -> Dict[str, Any]:
        """Fetch data from GraphQL endpoints"""
        try:
            transport = AIOHTTPTransport(url=endpoint)
            async with Client(
                transport=transport,
                fetch_schema_from_transport=True,
            ) as client:
                result = await client.execute(gql(query))
                return result
        except Exception as e:
            logging.error(f"GraphQL fetch error: {e}")
            return {}

    def _process_js_rendered_content(self, url: str) -> Dict[str, Any]:
        """Process JavaScript-rendered content"""
        try:
            self.driver.get(url)
            # Wait for dynamic content
            self.driver.implicitly_wait(5)
            
            # Get rendered content
            content = self.driver.page_source
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract text content
            text_content = ' '.join([
                p.get_text() 
                for p in soup.find_all(['p', 'div', 'section', 'article'])
            ])
            
            # Process with NLP
            return self.nlp_processor.analyze_text(text_content)
            
        except Exception as e:
            logging.error(f"Selenium processing error: {e}")
            return {}

    async def scrape_project(self, project_url: str) -> Dict[str, Any]:
        """Comprehensive project scraping"""
        results = {
            'web_content': {},
            'graphql_data': {},
            'decentralized_storage': {},
            'nlp_analysis': {}
        }
        
        # Scrape web content with JavaScript rendering
        web_content = self._process_js_rendered_content(project_url)
        results['web_content'] = web_content
        
        # Check for IPFS/Arweave links
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        for a in soup.find_all('a', href=True):
            if 'ipfs://' in a['href'] or 'ar://' in a['href']:
                storage_content = self.nlp_processor.process_decentralized_storage(
                    a['href']
                )
                if storage_content:
                    results['decentralized_storage'][a['href']] = storage_content
        
        # Fetch GraphQL data if available
        if 'graphql' in project_url or 'subgraph' in project_url:
            query = """
            {
              tokens {
                id
                name
                symbol
                totalSupply
              }
              # Add other relevant queries
            }
            """
            graphql_data = await self._fetch_graphql_data(project_url, query)
            results['graphql_data'] = graphql_data
        
        return results

    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'driver'):
            self.driver.quit()
