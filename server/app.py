from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/getfile', methods=['GET'])
def getfile():
    try:
        # Example data
        data = {
            "message": "Hello from the Flask API!",
            "status": "success",
            "data": {
                "items": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"},
                    {"id": 3, "name": "Item 3"}
                ]
            }
        }
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found", "status": "error"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
