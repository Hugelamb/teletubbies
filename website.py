from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

attack_data_store = {}
firewall_data_store = {}

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/attack")
def attack():
    return render_template('attack.html')

@app.route("/firewall")
def firewall_page():
    return render_template('firewall.html')

@app.route('/attack/<item_id>', methods=['PUT'])
def update_attack_item(item_id):
    if request.is_json:
        data = request.get_json()
        attack_data_store[item_id] = data
        
        socketio.emit('update', attack_data_store)

        return '', 200
    else:
        return jsonify({'error': 'Invalid input, expected JSON data'}), 400

@app.route('/firewall/<item_id>', methods=['PUT'])
def update_firewall_item(item_id):
    if request.is_json:
        data = request.get_json()
        firewall_data_store[item_id] = data
        
        socketio.emit('firewall_update', firewall_data_store)

        return '', 200
    else:
        return jsonify({'error': 'Invalid input, expected JSON data'}), 400

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)