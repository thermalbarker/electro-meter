from flask import Flask, request, jsonify, render_template
import sys
import logging
import asyncio
import threading
import json
import sml
import db
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

clients = set()

@app.route('/')
def hello_world():
    return render_template("index.html")

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

@sock.route('/sock')
def sock(ws):
    clients.add(ws)
    while True:
        try:
            data = ws.receive()
        except:
            clients.remove(ws)
            break

def printLatest(data):
    t, power, energy = data.getLatest()
    print(t, power, energy)

def readingCallback(sml_messages, data):
    db_write, connections = data
    secIndex, power, energy = sml.getReading(sml_messages)
    # Save to DB
    db_write.add(secIndex, power, energy)
    printLatest(db_write)
    # Broadcast to sockets
    for client in connections:
        client.send(json.dumps({ "secIndex": secIndex, "power": power, "energy": energy }))
    
def startReading(decoder):
    db_write = db.Db()
    db_write.setup()

    data = (db_write, clients)
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
