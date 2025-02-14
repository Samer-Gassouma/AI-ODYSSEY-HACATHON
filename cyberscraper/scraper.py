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

class CyberScraper:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self.tor_port = 9050
        self.tor_control_port = 9051
        self.content_analyzer = ContentAnalyzer()
        self.categories = [
            "sustainability",
            "environmental",
            "social responsibility",
            "governance",
            "blockchain",
            "crypto"
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
            async with session.get(url, headers=self._get_headers()) as response:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                
                content = {
                    'url': url,
                    'title': soup.title.string if soup.title else '',
                    'text_content': ' '.join([p.get_text() for p in soup.find_all(['p', 'div', 'section'])]),
                    'headers': [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])]
                }
                
                return self.content_analyzer.filter_content(content, self.categories)
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