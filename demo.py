import sml
import db
import logging, sys

el_db = None

def printLatest(data):
    secIndex, power, energy = data.getLatest()
    print(secIndex, power, energy)

def readingCallback(sml_messages, data):
    secIndex, power, energy = sml.getReading(sml_messages)
    data.add(secIndex, power, energy)
    printLatest(data)

def main():
    el_db = db.Db()
    el_db.setup()
    decoder = sml.SmlDecoder("/dev/ttyUSB0")
    decoder.readSml(readingCallback, el_db)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    main()

    
