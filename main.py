#!/bin/python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import gemini_slop
import cv2
import base64

from gemini_slop import StoreLayoutOptimizer

# --- GLOBAL INITIALIZATION ---
# Load raw historical data and floorplan into RAM once.
print("Loading historical data and floorplan...")
ai = StoreLayoutOptimizer()
ai.load_layout_mask("bin_mask.npy")
ai.load_customer_demands("data.txt")
print("AI ready to train on incoming subsets!")
# -----------------------------

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

        ai.generate_and_save_map(items, "empty_map.png", assets_dir="assets")

        print(items)
        img=cv2.imread("empty_map.png")
        png_img=cv2.imencode(".png",img)
        map_base64=base64.b64encode(png_img[1]).decode('utf-8')

        return jsonify({
            'status': 'success',
            'message': 'Product submitted successfully',
            'map_base64': map_base64
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(port=6969,debug=True)