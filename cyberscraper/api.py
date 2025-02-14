from flask import Flask, request, jsonify
from scraper import CyberScraper
import logging

app = Flask(__name__)
scraper = CyberScraper()

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.json.get('url')
    use_tor = request.json.get('use_tor', True)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    result = scraper.scrape(url, use_tor=use_tor)
    
    if result:
        return jsonify(result)
    return jsonify({'error': 'Scraping failed'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
