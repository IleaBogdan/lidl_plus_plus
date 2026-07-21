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
        map_id=0
        for key, value in request.form.items():
            if key == 'product':
                # Split by comma and strip whitespace
                for v in value.split(","):
                    item = v.strip()
                    if item:  # Only add non-empty items
                        items.append(item)
            elif key == 'mapId':
                map_id = value.strip()

        print("map id = "+str(map_id))
        # ai_bullshit(items)
        print(items)
        img=cv2.imread("shelves.png")
        png_img=cv2.imencode(".png",img)
        map_base64=base64.b64encode(png_img[1]).decode('utf-8')

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
