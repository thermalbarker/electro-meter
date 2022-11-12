import sml

def printValues(sml_messages):
    for sml_message in sml_messages:
        if type(sml_message.messageBody) is SmlList:
            for sml_entry in sml_message.messageBody.valList:
                print(sml_entry.getName(), ": ", sml_entry.getTime(), " ", sml_entry.getValue(), " ", sml_entry.getUnits())

def getPower(sml_messages):
    for sml_message in sml_messages:
        if type(sml_message.messageBody) is SmlList:
            for sml_entry in sml_message.messageBody.valList:
                if sml_entry.getUnits() == SmlUnit.W:
                    return sml_entry.getValue()
    return 0.0
    

def main():
    decoder = sml.SmlDecoder("/dev/ttyUSB0")
    power_array = []
    decoder.readSml(printValues)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    main()

    