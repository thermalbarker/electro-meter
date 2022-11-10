import serial
import logging, sys
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

class SmlSecIndex:
    secIndex = 0

    def __init__(self, secIndex):
        self.secIndex = secIndex


class SmlListEntry:
    objName = None
    status = None
    valTime = None
    unit = None
    scaler = None
    value = 0.0
    valueSignature = None

    def __init__(self, objName, status, valTime, unit, scalar, value, valueSignature):
        self.objName = objName
        self.status = status
        self.valTime = valTime
        self.unit = unit if unit != b'' else None
        self.scalar = scalar
        self.value = value
        self.valueSignature = valueSignature

    def getValue(self):
        return float(self.value) * 10 ** self.scalar if self.unit is not None else self.value

class SmlList:
    clientId = None
    serverId = None
    listName = None
    actSensorTime = None
    valList = None
    listSignature = None
    actGatewayTime = None

    def __init__(self, clientId, serverId, listName, actSensorTime, valList, listSignature, actGatewayTime):
        self.clientId = clientId
        self.serverId = serverId
        self.listName = listName
        self.actSensorTime = actSensorTime
        self.valList = valList
        self.listSignature = listSignature
        self.actGatewayTime = actGatewayTime

class SmlPublicClose:
    globalSignature = None

    def __init__(self, globalSignature):
        self.globalSignature = globalSignature

class SmlPublicOpen:
    codepage = None
    clientId = None
    reqFieldId = None
    serverId = None
    refTime = None
    smlVersion = None

    def __init__(self, codepage, clientId, reqFieldId, serverId, refTime, smlVersion):
        self.codepage = codepage
        self.clientId = clientId
        self.reqFieldId = reqFieldId
        self.serverId = serverId
        self.refTime = refTime
        self.smlVersion = smlVersion

class SmlMessage:
    transactionId = None
    groupNo = None
    abortOnError = None
    messageBody = None
    crc16 = None

    def __init__(self, transactionId, groupNo, abortOnError, messageBody, crc16):
        self.transactionId = transactionId
        self.groupNo = groupNo
        self.abortOnError = abortOnError
        self.messageBody = messageBody
        self.crc16 = crc16
    
class SmlDecoder:

    startMessage = b'\x01\x01\x01\x01'
    escapeSequence = b'\x1b\x1b\x1b\x1b'
    device = None
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
        logging.debug("Data byte: ", hex(data_type))
        if (data_type == 0x1b):
            val = None
        if (data_type & 0xF0) == 0x70:
            # List
            length = (data_type & 0x0F)
            val = []
            logging.debug("List length:", length)
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
                logging.debug("Octet:", val)
        elif (data_type == 0x52):
            val = int.from_bytes(self.device.read(1), "big", signed=True)
            logging.debug("Int8: ", val)
        elif (data_type == 0x53):
            val = int.from_bytes(self.device.read(2), "big", signed=True)
            logging.debug("Int16: ", val)
        elif (data_type == 0x55):
            val = int.from_bytes(self.device.read(4), "big", signed=True)
            logging.debug("Int32: ", val)
        elif (data_type == 0x59):
            val = int.from_bytes(self.device.read(8), "big", signed=True)
            logging.debug("Int32: ", val)
        elif (data_type == 0x62):
            val = self.device.read(1)[0]
            logging.debug("Uint8: ", val)
        elif (data_type == 0x63):
            val = int.from_bytes(self.device.read(2), "big")
            logging.debug("Uint16: ", val)
        elif (data_type == 0x65):
            val = int.from_bytes(self.device.read(4), "big")
            logging.debug("Uint32: ", val)
        elif (data_type == 0x69):
            val = int.from_bytes(self.device.read(8), "big")
            logging.debug("Uint64: ", val)
        return val

    def decodeMessage(self):
        while True:
            message = self.decodeObject()
            if message == None:
                logging.debug("**** End of message ****")
                break
            self.messages.append(message)
        logging.debug(self.messages)
        return SmlState.end
        
    def readSml(self, max = -1):
        n = 0
        state = SmlState.idle
        while True:
            next_state = SmlState.error
            logging.debug(state)
            if state == SmlState.idle:
                next_state = self.getEscapeSequence()
            elif state == SmlState.escape:
                next_state = self.getMessageStart()
            elif state == SmlState.error:
                next_state = SmlState.idle
            elif state == SmlState.message:
                next_state = self.decodeMessage()
            elif state == SmlState.end:
                n = n + 1
                next_state = SmlState.idle
                if max > 0 and n >= max:
                    break
            else:
                next_state = SmlState.error
            state = next_state

    def interpretTime(self, time):
        sml_time = None
        if isinstance(time, list) and len(time) >= 1:
            if time[0] == 0x01:
                # SecIndex
                sml_time = SmlSecIndex(time[1])
            # TODO: support other types
        return sml_time

    def interpretList(self, lst):
        sml_list = []
        for e in lst:
            sml_entry = SmlListEntry(e[0], e[1], self.interpretTime(e[2]), e[3], e[4], e[5], e[6])
            sml_list.append(sml_entry)
        return sml_list
            
    def interpretBody(self, body):
        sml_messageBody = None
        # PublicOpen.Res
        if body[0] == 0x00000101:
            po = body[1]
            sml_messageBody = SmlPublicOpen(po[0], po[1], po[2], po[3], self.interpretTime(po[4]), po[5])
        elif body[0] == 0x00000701:
            po = body[1]
            sml_messageBody = SmlList(po[0], po[1], po[2],self.interpretTime(po[3]), self.interpretList(po[4]), po[5], self.interpretTime(po[6]))
        elif body[0] == 0x00000201:
            po = body[1]
            sml_messageBody = SmlPublicClose(po[0])
        return sml_messageBody
        
    def interpretMessages(self):
        sml_messages = []
        while self.messages:
            m = self.messages.pop(0)
            if isinstance(m, list) and len(m) >= 6:
                sml_message = SmlMessage(m[0], m[1], m[2], self.interpretBody(m[3]), m[4])
                sml_messages.append(sml_message)
        logging.debug(sml_messages)
        return sml_messages

def printValues(sml_messages):
    for sml_message in sml_messages:
        if type(sml_message.messageBody) is SmlList:
            for sml_entry in sml_message.messageBody.valList:
                logging.info(sml_entry.getValue())
    
def main():
    decoder = SmlDecoder("/dev/ttyUSB0")
    while True:
        decoder.readSml(1)
        sml_messages = decoder.interpretMessages()
        printValues(sml_messages)

if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    main()

    
