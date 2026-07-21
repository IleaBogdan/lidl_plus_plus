#!/bin/python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import base64

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
        img=cv2.imread("empty_map.png")
        jpg_img=cv2.imencode(".png  ",img)
        map_base64=base64.b64encode(jpg_img[1]).decode('utf-8')

        # Success response with 200
        return jsonify({
            'status': 'success',
            'message': 'Product submitted successfully',
            'items': items,
            'map_url': map_base64
        }), 200

        
    except Exception as e:
        # Error response with 500
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(port=6969,debug=True)
