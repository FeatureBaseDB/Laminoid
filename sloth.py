from InstructorEmbedding import INSTRUCTOR
model = INSTRUCTOR('hkunlp/instructor-large')

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/embed', methods=['POST'])
def embed():
    if request.method == 'POST':
        data = request.json  # Assuming the data is sent as JSON in the request body

        embeddings = model.encode(["consider the animal type:", data.get('sentence')]).tolist()

        # Process the data and generate a response
        response_data = {
            "message": "Received POST request at /embed",
            "embeddings": embeddings
        }

        return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)