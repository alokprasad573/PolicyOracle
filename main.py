import os, re, json
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')


@app.route('/', methods=['GET'])
def index():
    return render_template('home.html')



if __name__ == '__main__':
    from waitress import serve
    # Use PORT from environment or default to 3000
    port = int(os.environ.get('PORT', 3000))
    
    print("-" * 50)
    print(f"PolicyOracle Server is running!")
    print(f"Local:   http://localhost:{port}")
    print(f"Network: http://0.0.0.0:{port}")
    print("-" * 50)
    
    serve(app, host='0.0.0.0', port=port, debug=True)
    
