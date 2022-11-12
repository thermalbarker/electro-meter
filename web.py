from flask import Flask
import threading
import sml
import db

app = Flask(__name__)
el_db = db.Db()

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

if __name__ == '__main__':
    el_db.setup()
    decoder = sml.SmlDecoder("/dev/ttyUSB0")
    bg_thread = threading.Thread(target = decoder.readSml, args = (readingCallback, el_db))
    bg_thread.start()
    app.run()
    decoder.stopReading()
    bg_thread.join()