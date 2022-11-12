from flask import Flask
import threading
import sml
import db

app = Flask(__name__)

db_read = db.Db()

@app.route('/')
def hello_world():
    secIndex, power, energy = el_db.getLatest()
    return str(secIndex, power, energy)

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

if __name__ == '__main__':
    db_read.setup()
    decoder = sml.SmlDecoder("/dev/ttyUSB0")
    bg_thread = threading.Thread(target = startReading, args = decoder)
    bg_thread.start()
    app.run()
    decoder.stopReading()
    bg_thread.join()