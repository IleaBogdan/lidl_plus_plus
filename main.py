#!/bin/python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import gemini_slop
import cv2
import base64

# --- ADDED: Import and initialize the AI once on startup ---
from gemini_slop import StoreLayoutOptimizer
print("Initializing and Training AI...")
ai = StoreLayoutOptimizer()
ai.load_layout_mask("bin_mask.npy")
ai.load_customer_demands("train_data/data.txt")
ai.prepare_optimization()
ai.train(epochs=100)  # Learns the optimal store layout
print("AI Ready to serve requests!")
# ---------------------------------------------------------

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

        ai.generate_and_save_map(items, "empty_map.png", assets_dir="assets")

        print(items)
        img=cv2.imread("empty_map.png")
        png_img=cv2.imencode(".png",img)
        map_base64=base64.b64encode(png_img[1]).decode('utf-8')
        
        # Success response with 200
        return jsonify({
            'status': 'success',
            'message': 'Product submitted successfully',
            'map_base64': map_base64
        }), 200
    
    except Exception as e:
        # Error response with 500
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(port=6969,debug=True)
