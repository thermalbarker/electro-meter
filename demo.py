import sml
import db
import logging, sys

el_db = None

def printLatest(data):
    secIndex, power, energy = data.getLatest()
    print(secIndex, power, energy)

def getReading(sml_messages):
    secIndex = -1
    power = 0.0
    energy = 0.0
    for sml_message in sml_messages:
        if type(sml_message.messageBody) is sml.SmlList:
            for sml_entry in sml_message.messageBody.valList:
                if sml_entry.getTime() >= 0:
                    secIndex = sml_entry.getTime()
                if sml_entry.getUnits() == sml.SmlUnit.W:
                    power = sml_entry.getValue()
                if sml_entry.getUnits() == sml.SmlUnit.Wh:
                    energy = sml_entry.getValue()
    return secIndex, power, energy

def readingCallback(sml_messages, data):
    secIndex, power, energy = getReading(sml_messages)
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

    
