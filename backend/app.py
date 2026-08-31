from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/api/match", methods=["POST"])
def parse():
    data = request.json
    text = data["text"]

    print("Received:", text)

    return jsonify({
        "message": "Successfully received text!",
        "text": text
    })

if __name__ == "__main__":
    app.run(port=8000, debug=True)