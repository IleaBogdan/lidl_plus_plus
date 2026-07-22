#!/bin/python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import gemini_slop

app = Flask(__name__)
CORS(app)

pipeline=None

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

        print(items)
        arrangement = pipeline.arrange_products(items)

        # Success response with 200
        return jsonify({
            'status': 'success',
            'message': 'Product submitted successfully',
            'aisle_lengths': pipeline.aisle_lengths,
            'aisles': arrangement
        }), 200
    
    except Exception as e:
        # Error response with 500
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

if __name__ == '__main__':
    pipeline=gemini_slop.StoreOptimizationPipeline()
    app.run(port=6969,debug=True)
