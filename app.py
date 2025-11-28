from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

def extract_shortcode(url):
    """Extract shortcode from Instagram URL"""
    pattern = r'instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def get_instagram_caption(url):
    """Get caption from Instagram post using Instaloader"""
    shortcode = extract_shortcode(url)
    
    if not shortcode:
        return None, "Invalid Instagram URL format"
    
    L = instaloader.Instaloader()
    
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        return {
            'caption': post.caption,
            'username': post.owner_username,
            'likes': post.likes,
            'comments': post.comments,
            'date': post.date_utc.isoformat(),
            'is_video': post.is_video,
            'shortcode': shortcode
        }, None
    except instaloader.exceptions.QueryReturnedNotFoundException:
        return None, "Post not found (may be deleted or private)"
    except instaloader.exceptions.LoginRequiredException:
        return None, "This is a private account - login required"
    except instaloader.exceptions.TooManyRequestsException:
        return None, "Rate limited by Instagram - please try again later"
    except Exception as e:
        return None, f"Error: {str(e)}"

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Instagram Caption Extractor API is running'})

@app.route('/extract', methods=['POST'])
def extract_caption():
    """
    Extract caption from Instagram post
    
    Expected JSON body:
    {
        "url": "https://www.instagram.com/reel/ABC123/"
    }
    """
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing "url" parameter in request body'
        }), 400
    
    url = data['url']
    
    if not url or not isinstance(url, str):
        return jsonify({
            'success': False,
            'error': 'Invalid URL format'
        }), 400
    
    result, error = get_instagram_caption(url)
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

@app.route('/extract-simple', methods=['GET'])
def extract_caption_simple():
    """
    Simple GET endpoint for quick testing
    Usage: /extract-simple?url=https://www.instagram.com/reel/ABC123/
    """
    url = request.args.get('url')
    
    if not url:
        return jsonify({
            'success': False,
            'error': 'Missing "url" query parameter'
        }), 400
    
    result, error = get_instagram_caption(url)
    
    if error:
        return jsonify({
            'success': False,
            'error': error
        }), 400
    
    return jsonify({
        'success': True,
        'data': result
    }), 200

if __name__ == '__main__':
    print("=" * 50)
    print("Instagram Caption Extractor API")
    print("=" * 50)
    print("\nAPI Endpoints:")
    print("  GET  /health           - Health check")
    print("  POST /extract          - Extract caption (JSON body)")
    print("  GET  /extract-simple   - Extract caption (query param)")
    print("\nStarting server on http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
