import requests
import concurrent.futures
import random
from bs4 import BeautifulSoup
import time

class ProxyManager:
    def __init__(self):
        self.proxies = set()
        self.working_proxies = set()
        self.test_url = 'http://httpbin.org/ip'
        
    def fetch_free_proxies(self):
        sources = [
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
            'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt'
        ]
        
        for source in sources:
            try:
                response = requests.get(source, timeout=10)
                proxies = response.text.strip().split('\n')
                self.proxies.update(proxies)
            except:
                continue
                
    def verify_proxy(self, proxy):
        try:
            proxy_dict = {
                'http': f'http://{proxy}',
                'https': f'http://{proxy}'
            }
            response = requests.get(
                self.test_url,
                proxies=proxy_dict,
                timeout=10
            )
            if response.status_code == 200:
                self.working_proxies.add(proxy)
                return True
        except:
            return False
            
    def get_working_proxies(self, max_workers=50):
        self.fetch_free_proxies()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(self.verify_proxy, self.proxies)
        return list(self.working_proxies)
    
    def get_random_proxy(self):
        if not self.working_proxies:
            self.get_working_proxies()
        return random.choice(list(self.working_proxies)) if self.working_proxies else None
