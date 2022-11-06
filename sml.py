import serial
from enum import Enum

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
        elif (data_type == 0x62):
            val = self.device.read(1)[0]
            print("Uint8: ", val)
        elif (data_type == 0x63):
            val = int.from_bytes(self.device.read(2), "big")
            print("Uint16: ", val)
        elif (data_type == 0x65):
            val = int.from_bytes(self.device.read(4), "big")
            print("Uint32: ", val)
        return val

    def decodeMessage(self):
        message = self.decodeObject()
        print(message)
        if message:
            return SmlState.end
        else:
            return SmlState.error
        
    def readSml(self):
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
                next_state = self.getMESSmlState.idle
            else:
                next_state = SmlState.error
            self.state = next_state


def main():
    decoder = SmlDecoder("/dev/ttyUSB0")
    decoder.readSml()


if __name__ == "__main__":
    main()

    
