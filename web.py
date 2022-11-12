from flask import Flask
import threading
import sml
import db

app = Flask(__name__)

@app.route('/')
def hello_world():
    db_read = db.Db()
    db_read.setup()
    secIndex, power, energy = db_read.getLatest()
    db_read.disconnect()
    return "Time: {0} Power: {1} Total: {2}".format(secIndex, power, energy)

def printLatest(data):
    t, power, energy = data.getLatest()
    print(t, power, energy)

def readingCallback(sml_messages, data):
    secIndex, power, energy = sml.getReading(sml_messages)
    data.add(secIndex, power, energy)
    printLatest(data)

def startReading(decoder):
    db_write = db.Db()
    db_write.setup()
    decoder.readSml(readingCallback, db_write)
    db_write.disconnect()
    
if __name__ == '__main__':
    decoder = sml.SmlDecoder("/dev/ttyUSB0")
    bg_thread = threading.Thread(target = startReading, args = (decoder, ))
    bg_thread.start()
    app.run(host='0.0.0.0')
    decoder.stopReading()
    bg_thread.join()
