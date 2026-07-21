from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/submit', methods=['POST'])
def submitProduct():
    try:
        items = []
        for key, value in request.form.items():
            for v in value.split(","):
                items.append(v.strip())
        
        # ai_bullshit(items)
        print(items)
        
        # Success response with 200
        return jsonify({
            'status': 'success',
            'message': 'Product submitted successfully',
            'items': items
        }), 200
        
    except Exception as e:
        # Error response with 500
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(port=6969,debug=True)
