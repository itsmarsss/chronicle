from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/api/gettext', methods=['GET'])
def gettext():
    try:
        text = request.args.get('text')
        if not text:
            return jsonify({"error": "Text parameter is required", "status": "error"}), 400
            
        # Save text to file in root directory
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(root_dir, 'temp/text.txt')
        
        try:
            with open(file_path, 'w') as f:
                f.write(text)
        except IOError as e:
            return jsonify({"error": f"Failed to save text: {str(e)}", "status": "error"}), 500
            
        data = {
            "message": "Text saved successfully",
            "status": "success",
            "data": {
                "input_text": text,
                "saved_to": file_path
            }
        }

        os.system("cd " + root_dir + " && ./parser/run-txt.sh")

        f = open(root_dir + "/temp/characters.json")
        first = f.read()

        return first
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file.save(root_dir + "/temp/input.pdf")
    os.system('cd ' + root_dir + ' && ./parser/run-pdf.sh')
    f = open(root_dir + "/temp/characters.json")
    first = f.read()

    return first
    return jsonify({'message': 'File uploaded successfully'}), 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Resource not found", "status": "error"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
