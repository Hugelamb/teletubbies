from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

data_storage = {}

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/attack")
def attack():
    return render_template('attack.html')

@app.route('/attack/<item_id>', methods=['PUT'])
def update_item(item_id):
    if request.is_json:
        data = request.get_json()
        data_storage[item_id] = data
        
        socketio.emit('update', data_storage)

        return '', 200
    else:
        return jsonify({'error': 'Invalid input, expected JSON data'}), 400

@app.route('/firewall/<item_id>', methods=['PUT'])
def update_firewall_item(item_id):
    if request.is_json:
        data = request.get_json()
        data_storage[item_id] = data
        
        socketio.emit('update', data_storage)

        return '', 200
    else:
        return jsonify({'error': 'Invalid input, expected JSON data'}), 400

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
