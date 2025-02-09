from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/proxy', methods=['POST'])
def proxy_request():
    try:
        data = request.json
        prompt = data.get('prompt')
        model = data.get('model', "anthropic/claude-3-opus-20240229")  # Default model if none specified
        
        # Get a random API key from environment variables
        api_keys = [key for key in os.environ.keys() if key.startswith('OPENROUTER_API_KEY_')]
        if not api_keys:
            return jsonify({"error": "No API keys configured"}), 500
        
        selected_key = os.environ[random.choice(api_keys)]
        
        headers = {
            "Authorization": f"Bearer {selected_key}",
            "HTTP-Referer": request.headers.get('Origin', 'https://stealth-typer.onrender.com'),
            "Content-Type": "application/json"
        }
        
        # Handle Gemini image processing
        if "gemini" in model.lower() and isinstance(prompt, str) and any(ext in prompt.lower() for ext in [".png", ".jpg", ".jpeg"]):
            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What is in this image?"},
                        {"type": "image_url", "image_url": {"url": prompt}}
                    ]
                }]
            }
        else:
            payload = {
                "model": model,
                "messages": [{
                    "role": "user",
                    "content": prompt
                }]
            }
        
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        response.raise_for_status()
        return jsonify(response.json())
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"OpenRouter API error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Ensure at least one API key is configured
    if not any(key.startswith('OPENROUTER_API_KEY_') for key in os.environ.keys()):
        print("Warning: No OpenRouter API keys configured. Set OPENROUTER_API_KEY_1, OPENROUTER_API_KEY_2, etc.")
    
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port) 
