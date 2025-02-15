import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
from proxy_manager import ProxyManager
import logging
import socks
import socket
from stem import Signal
from stem.control import Controller
from content_analyzer import ContentAnalyzer
from urllib.parse import urljoin
import asyncio
import aiohttp
from data_cleaner import DataCleaner
import os
from dotenv import load_dotenv
from ml_esg_scorer import MLESGScorer
from advanced_scraper import AdvancedScraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, Any, Optional
from functools import lru_cache

load_dotenv()

class CyberScraper:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self.tor_port = 9050
        self.tor_control_port = 9051
        self.content_analyzer = ContentAnalyzer()
        self.data_cleaner = DataCleaner(os.getenv('GEMINI_API_KEY'))
        self.esg_scorer = MLESGScorer()
        self.advanced_scraper = AdvancedScraper()
        self.categories = [
            "sustainability",
            "environmental",
            "social responsibility",
            "governance",
            "blockchain",
            "crypto",
            "cybersecurity threat",
            "vulnerability disclosure",
            "security advisory",
            "data breach",
            "malware analysis",
            "cyber attack",
            "security patch",
            "exploit code",
            "security research",
            "incident response"
        ]
        
    def _get_tor_session(self):
        session = requests.session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        return session
        
    def _renew_tor_ip(self):
        try:
            with Controller.from_port(port=self.tor_control_port) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                time.sleep(5)
        except:
            logging.error("Failed to renew Tor IP")
            
    def _get_headers(self):
        return {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
    async def _scrape_tab(self, session, url):
        try:
            # Get basic content first
            async with session.get(url, headers=self._get_headers()) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                content = {
                    'url': url,
                    'title': soup.title.string if soup.title else '',
                    'text_content': ' '.join([p.get_text() for p in soup.find_all(['p', 'div', 'section'])]),
                    'headers': [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])]
                }
                
                # Use advanced scraping capabilities
                advanced_results = await self.advanced_scraper.scrape_project(url)
                
                # Merge the results
                filtered_content = self.content_analyzer.filter_content(content, self.categories)
                if filtered_content:
                    cleaned_data = self.data_cleaner.structure_scraped_data(
                        filtered_content.get('text_content', '')
                    )
                    if cleaned_data:
                        filtered_content['cleaned_data'] = cleaned_data
                        filtered_content['ml_esg_analysis'] = self.esg_scorer.calculate_esg_score(cleaned_data)
                        
                    # Add advanced analysis results
                    filtered_content['advanced_analysis'] = {
                        'nlp_results': advanced_results['web_content'],
                        'decentralized_storage': advanced_results['decentralized_storage'],
                        'graphql_data': advanced_results['graphql_data']
                    }
                    
                return filtered_content
        except Exception as e:
            logging.error(f"Tab scraping error: {str(e)}")
            return None

    async def _scrape_all_tabs(self, base_url):
        async with aiohttp.ClientSession() as session:
            soup = BeautifulSoup(await (await session.get(base_url)).text(), 'html.parser')
            nav_links = [
                urljoin(base_url, a['href']) 
                for a in soup.find_all('a', href=True) 
                if 'about' in a['href'].lower() or 
                   'sustainability' in a['href'].lower() or
                   'governance' in a['href'].lower() or
                     'esg' in a['href'].lower() or
                     'social' in a['href'].lower() or
                        'environment' in a['href'].lower() or
                        'sustainable' in a['href'].lower() or
                        'responsibility' in a['href'].lower() or
                        'blockchain' in a['href'].lower() or
                        'crypto' in a['href'].lower()
                        
            ]
            
            tasks = [self._scrape_tab(session, url) for url in nav_links]
            results = await asyncio.gather(*tasks)
            return {url: result for url, result in zip(nav_links, results) if result}

    def scrape(self, url, use_tor=True):
        try:
            session = self._get_tor_session() if use_tor else self.session
            
            if not use_tor:
                proxy = self.proxy_manager.get_random_proxy()
                if proxy:
                    session.proxies = {
                        'http': f'http://{proxy}',
                        'https': f'http://{proxy}'
                    }
            
            results = asyncio.run(self._scrape_all_tabs(url))
            
            # Cleanup Selenium resources
            self.advanced_scraper.cleanup()
            
            return {
                'base_url': url,
                'relevant_content': results
            }
            
        except Exception as e:
            logging.error(f"Scraping error: {str(e)}")
            return None
            
        finally:
            if use_tor:
                self._renew_tor_ip()

    def _setup_tor_proxy(self) -> None:
        """Configure Tor proxy settings"""
        self.PROXY = "socks5h://localhost:9050"
        
    def _setup_chrome_options(self, use_tor: bool = True) -> Options:
        """Configure Chrome options for scraping"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        if use_tor:
            self._setup_tor_proxy()
            chrome_options.add_argument(f'--proxy-server={self.PROXY}')
            
        return chrome_options

    def _extract_text_content(self, element) -> str:
        """Extract clean text content from HTML element"""
        try:
            return ' '.join(element.stripped_strings)
        except Exception:
            return ""

    def _parse_html_content(self, html: str) -> Dict[str, Any]:
        """Parse HTML and extract relevant content"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            content = {}
            
            # Extract title
            if soup.title:
                content['title'] = self._extract_text_content(soup.title)
                
            # Extract main content
            for tag in ['article', 'main', '[role="main"]']:
                main_content = soup.select_one(tag)
                if main_content:
                    content['main_content'] = self._extract_text_content(main_content)
                    break
                    
            # Extract paragraphs
            paragraphs = []
            for p in soup.find_all('p'):
                text = self._extract_text_content(p)
                if len(text) > 50:  # Filter out short paragraphs
                    paragraphs.append(text)
            content['paragraphs'] = paragraphs
            
            # Extract headings
            headings = []
            for h in soup.find_all(['h1', 'h2', 'h3']):
                text = self._extract_text_content(h)
                if text:
                    headings.append(text)
            return content
            
        except Exception as e:
            logging.error(f"HTML parsing failed: {str(e)}")
            return {}

    def _get_new_tor_identity(self):
        """Request new Tor identity"""
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
                time.sleep(5)  # Wait for new identity
        except Exception as e:
            logging.error(f"Tor identity rotation failed: {str(e)}")

    @lru_cache(maxsize=100)
    def scrape(self, url: str, use_tor: bool = True) -> Optional[Dict[str, Any]]:
        """
        Scrape URL and analyze content for cybersecurity relevance
        
        Args:
            url: Target URL
            use_tor: Whether to route traffic through Tor
            
        Returns:
            Dictionary of relevant content or None if failed
        """
        try:
            if use_tor:
                self._get_new_tor_identity()
                
            options = self._setup_chrome_options(use_tor)
            driver = webdriver.Chrome(options=options)
            
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Let JavaScript content load
                time.sleep(2)
                
                # Get page content
                html_content = driver.page_source
                parsed_content = self._parse_html_content(html_content)
                
                # Analyze content
                filtered_content = self.content_analyzer.filter_content(
                    parsed_content, 
                    self.categories
                )
                
                return filtered_content
                
            finally:
                driver.quit()
                
        except Exception as e:
            logging.error(f"Scraping failed: {str(e)}")
            return None