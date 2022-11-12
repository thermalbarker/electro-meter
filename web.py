from flask import Flask, request, jsonify, send_from_directory
import threading
import json
import sml
import db
import ws

app = Flask(__name__)

@app.route('/')
def hello_world():
    db_read = db.Db()
    db_read.setup()
    secIndex, power, energy = db_read.getLatest()
    db_read.disconnect()
    #return "Time: {0} Power: {1} Total: {2}".format(secIndex, power, energy)
    return send_from_directory('web', 'index.html')

@app.route('/api/reading', methods=['GET'])
def get_latest():
    db_read = db.Db()
    db_read.setup()
    reading = db_read.getLatestDict()
    db_read.disconnect()
    return jsonify(reading)

@app.route('/api/readings', methods=['GET'])
def get_readings():
    args = request.args
    limit = args.get('limit', -1)
    db_read = db.Db()
    db_read.setup()
    reading = db_read.getReadings(limit)
    db_read.disconnect()
    return jsonify(reading)

def printLatest(data):
    t, power, energy = data.getLatest()
    print(t, power, energy)

def readingCallback(sml_messages, data):
    db_write, ws_server = data
    secIndex, power, energy = sml.getReading(sml_messages)
    # Save to DB
    db_write.add(secIndex, power, energy)
    printLatest(db_write)
    # Broadcast to sockets
    ws_server.send_to_clients(json.dumps({ "secIndex": secIndex, "power": power, "energy": energy }))

def startReading(decoder):
    ws_server = ws.Server()
    db_write = db.Db()
    db_write.setup()

    data = (db_write, ws_server)
    decoder.readSml(readingCallback, data)
    db_write.disconnect()
    
if __name__ == '__main__':
    # Data acquistion
    decoder = sml.SmlDecoder("/dev/ttyUSB0")
    bg_thread = threading.Thread(target = startReading, args = (decoder, ))
    bg_thread.start()

    # Web Server
    app.run(host='0.0.0.0')

    # Cleanup
    decoder.stopReading()
    bg_thread.join()
