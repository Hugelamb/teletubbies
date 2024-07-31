from flask import Flask, request, jsonify

app = Flask(__name__)

data_storage = {}

@app.route("/")
def main():
    return f"<p>{data_storage}<p>"

@app.route('/update/<item_id>', methods=['PUT'])
def update_item(item_id):
    if request.is_json:
        data = request.get_json()
        
        print(f"Received data: {data}")
        
        data_storage[item_id] = data
        
        print(f"Updated storage: {data_storage}")
        
        return jsonify({'message': 'Item updated successfully', 'item': data}), 200
    else:
        return jsonify({'error': 'Invalid input, expected JSON data'}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
