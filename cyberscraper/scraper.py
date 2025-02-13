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

class RobustScraper:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.user_agent = UserAgent()
        self.session = requests.Session()
        self.tor_port = 9050
        self.tor_control_port = 9051
        
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
            
            response = session.get(
                url,
                headers=self._get_headers(),
                timeout=30,
                verify=False
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            data = {
                'url': url,
                'title': soup.title.string if soup.title else '',
                'text_content': ' '.join([p.get_text() for p in soup.find_all(['p', 'div', 'section'])]),
                'links': [a.get('href') for a in soup.find_all('a', href=True)],
                'headers': [h.get_text() for h in soup.find_all(['h1', 'h2', 'h3'])],
                'meta_tags': {
                    meta.get('name', meta.get('property', '')): meta.get('content', '')
                    for meta in soup.find_all('meta')
                }
            }
            
            return data
            
        except Exception as e:
            logging.error(f"Scraping error: {str(e)}")
            return None
            
        finally:
            if use_tor:
                self._renew_tor_ip()
