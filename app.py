from flask import Flask, request, jsonify
import os
import sys

# Import the scraper function
sys.path.append(os.path.dirname(__file__))
from scraper import scrape_vfx_companies

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'VFX Company Scraper API',
        'endpoints': {
            '/scrape': 'POST - Scrape VFX companies',
            '/health': 'GET - Health check'
        },
        'usage': {
            'method': 'POST',
            'endpoint': '/scrape',
            'body': {
                'search_query': 'your search query here'
            }
        }
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        
        if not data or 'search_query' not in data:
            return jsonify({
                'error': 'Missing search_query in request body'
            }), 400
        
        search_query = data['search_query']
        
        # Check if API key is configured
        api_key = os.getenv('SARVAM_API_KEY')
        if not api_key:
            return jsonify({
                'error': 'SARVAM_API_KEY environment variable not configured'
            }), 500
        
        # Call the scraper function
        result = scrape_vfx_companies(search_query, api_key)
        
        return jsonify({
            'success': True,
            'data': result
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
