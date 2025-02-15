from flask import Flask, request, jsonify, render_template
from scraper import CyberScraper
import logging
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
scraper = CyberScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/scrape', methods=['POST'])
def scrape_url():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({"error": "No URL provided"}), 400
            
        url = data['url']
        use_tor = data.get('use_tor', True)
        
        results = scraper.scrape(url, use_tor=use_tor)
        if results:
            return jsonify(results)
        else:
            return jsonify({"error": "Scraping failed"}), 500
            
    except Exception as e:
        logging.error(f"API error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
