import serial
from enum import Enum

# Some useful links
# https://de.wikipedia.org/wiki/Smart_Message_Language
# https://www.bsi.bund.de/SharedDocs/Downloads/DE/BSI/Publikationen/TechnischeRichtlinien/TR03109/TR-03109-1_Anlage_Feinspezifikation_Drahtgebundene_LMN-Schnittstelle_Teilb.pdf?__blob=publicationFile


class SmlState(Enum):
    idle = 0
    escape = 1
    message = 2
    end = 3
    error = 4

    
class SmlDecoder:

    startMessage = b'\x01\x01\x01\x01'
    escapeSequence = b'\x1b\x1b\x1b\x1b'
    device = None
    state = SmlState.idle
    messages = []
    
    def __init__(self, device):
        self.device = serial.Serial(device, 9600, timeout=3)

    def getEscapeSequence(self):
        escape = self.device.read_until(self.escapeSequence)
        if escape.endswith(self.escapeSequence):
            return SmlState.escape
        else:
            return SmlState.error

    def getMessageStart(self):
        start = self.device.read(len(self.startMessage))
        if start.startswith(self.startMessage):
            return SmlState.message
        else:
            return SmlState.error

    def decodeObject(self):
        val = None
        data_type = self.device.read()[0]
        print("Data byte: ", hex(data_type))
        if (data_type == 0x1b):
            val = None
        if (data_type & 0xF0) == 0x70:
            # List
            length = (data_type & 0x0F)
            val = []
            print("List length:", length)
            for i in range(length):
                element = self.decodeObject()
                if element == None:
                    val = None
                    break
                val.append(element)
        elif (data_type & 0xF0) == 0x00:
            # Octet String
            length = (data_type & 0x0F)
            val = b''
            if length > 1:
                val = self.device.read(length - 1)
                print("Octet:", val)
        elif (data_type == 0x52):
            val = int.from_bytes(self.device.read(1), "big", signed=True)
            print("Int8: ", val)
        elif (data_type == 0x53):
            val = int.from_bytes(self.device.read(2), "big", signed=True)
            print("Int16: ", val)
        elif (data_type == 0x55):
            val = int.from_bytes(self.device.read(4), "big", signed=True)
            print("Int32: ", val)
        elif (data_type == 0x59):
            val = int.from_bytes(self.device.read(8), "big", signed=True)
            print("Int32: ", val)
        elif (data_type == 0x62):
            val = self.device.read(1)[0]
            print("Uint8: ", val)
        elif (data_type == 0x63):
            val = int.from_bytes(self.device.read(2), "big")
            print("Uint16: ", val)
        elif (data_type == 0x65):
            val = int.from_bytes(self.device.read(4), "big")
            print("Uint32: ", val)
        elif (data_type == 0x69):
            val = int.from_bytes(self.device.read(8), "big")
            print("Uint64: ", val)
        return val

    def decodeMessage(self):
        while True:
            message = self.decodeObject()
            if message == None:
                print("**** End of message ****")
                break
            self.messages.append(message)
        print(self.messages)
        return SmlState.end
        
    def readSml(self, max = -1):
        n = 0
        while True:
            next_state = SmlState.error
            print(self.state)
            if self.state == SmlState.idle:
                next_state = self.getEscapeSequence()
            elif self.state == SmlState.escape:
                next_state = self.getMessageStart()
            elif self.state == SmlState.error:
                next_state = SmlState.idle
            elif self.state == SmlState.message:
                next_state = self.decodeMessage()
            elif self.state == SmlState.end:
                n = n + 1
                if max > 0 and n >= max:
                    break
                else:
                    next_state = SmlState.idle
            else:
                next_state = SmlState.error
            self.state = next_state

    def interpretBody(self, body):
        sml_messageBody = {}
        # PublicOpen.Res
        if body[0] == 0x00000101:
            po = body[1]
            sml_messageBody["type"] = "SML_PublicOpen.Res"
            sml_messageBody["codepage"] = po[0]
            sml_messageBody["clientId"] = po[1]
            sml_messageBody["reqFieldId"] = po[2]
            sml_messageBody["serverId"] = po[3]
            sml_messageBody["refTime"] = po[4]
            sml_messageBody["smlVersion"] = po[5]
        elif body[0] == 0x00000701:
            po = body[1]
            sml_messageBody["type"] = "SML_GetList.Res"
            sml_messageBody["clientId"] = po[0]
            sml_messageBody["serverId"] = po[1]
            sml_messageBody["listName"] = po[2]
            sml_messageBody["actSensorTime"] = po[3]
            sml_messageBody["valList"] = po[4]
            sml_messageBody["listSignature"] = po[5]
            sml_messageBody["actGatewayTime"] = po[6]
        elif body[0] == 0x00000201:
            po = body[1]
            sml_messageBody["type"] = "SML_PublicClose.Res"
            sml_messageBody["globalSignature"] = po[0]
        return sml_messageBody
        
    def interpretMessages(self):
        sml_messages = []
        for m in self.messages:
            if isinstance(m, list) and len(m) >= 6:
                sml_message = {}
                sml_message["transactionId"] = m[0]
                sml_message["groupNo"] = m[1]
                sml_message["abortOnError"] = m[2]
                sml_message["messageBody"] = self.interpretBody(m[3])
                sml_message["crc16"] = m[4]
                sml_message["endOfSmlMsg"] = m[5]
                sml_messages.append(sml_message)
        print(sml_messages)
            

def main():
    decoder = SmlDecoder("/dev/ttyUSB0")
    decoder.readSml(1)
    decoder.interpretMessages()


if __name__ == "__main__":
    main()

    
