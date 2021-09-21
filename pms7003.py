# Taken from https://github.com/pkucmus/micropython-pms7003 with fixes.
import machine
import struct
import time


class UartError(Exception):
    pass


class Pms7003:
    START_BYTE_1 = 0x42
    START_BYTE_2 = 0x4d

    PMS_FRAME_LENGTH = 0
    PMS_PM1_0 = 1
    PMS_PM2_5 = 2
    PMS_PM10_0 = 3
    PMS_PM1_0_ATM = 4
    PMS_PM2_5_ATM = 5
    PMS_PM10_0_ATM = 6
    PMS_PCNT_0_3 = 7
    PMS_PCNT_0_5 = 8
    PMS_PCNT_1_0 = 9
    PMS_PCNT_2_5 = 10
    PMS_PCNT_5_0 = 11
    PMS_PCNT_10_0 = 12
    PMS_VERSION = 13
    PMS_ERROR = 14
    PMS_CHECKSUM = 15

    SLEEP_REQUEST = bytearray(
        [START_BYTE_1, START_BYTE_2, 0xe4, 0x00, 0x00, 0x01, 0x73]
    )

    WAKEUP_REQUEST = bytearray(
        [START_BYTE_1, START_BYTE_2, 0xe4, 0x00, 0x01, 0x01, 0x74]
    )

    def __init__(self):
        self.uart = machine.UART(
            1, rx=25, tx=26, baudrate=9600, bits=8, parity=None, stop=1)

    def __repr__(self):
        return "Pms7003({})".format(self.uart)

    @staticmethod
    def _assert_byte(byte, expected):
        if byte is None or len(byte) < 1 or ord(byte) != expected:
            return False
        return True

    @staticmethod
    def _format_bytearray(buffer):
        return "".join("0x{:02x} ".format(i) for i in buffer)

    def _send_cmd(self, request, response):

        nr_of_written_bytes = self.uart.write(request)

        if nr_of_written_bytes != len(request):
            raise UartError('Failed to write to UART')

        if response:
            time.sleep(2)
            buffer = self.uart.read(len(response))

            if buffer != response:
                raise UartError(
                    'Wrong UART response, expecting: {}, getting: {}'.format(
                        Pms7003._format_bytearray(
                            response), Pms7003._format_bytearray(buffer)
                    )
                )

    def sleep(self):
        self._send_cmd(request=Pms7003.SLEEP_REQUEST, response=None)

    def wakeup(self):
        self._send_cmd(request=Pms7003.WAKEUP_REQUEST, response=None)

    def read(self):
        while True:
            first_byte = self.uart.read(1)
            if not self._assert_byte(first_byte, Pms7003.START_BYTE_1):
                continue

            second_byte = self.uart.read(1)
            if not self._assert_byte(second_byte, Pms7003.START_BYTE_2):
                continue

            # we are reading 30 bytes left
            read_bytes = self.uart.read(30)
            if len(read_bytes) < 30:
                continue

            data = struct.unpack('!HHHHHHHHHHHHHBBH', read_bytes)

            checksum = Pms7003.START_BYTE_1 + Pms7003.START_BYTE_2
            checksum += sum(read_bytes[:28])

            if checksum != data[Pms7003.PMS_CHECKSUM]:
                continue

            return {
                'FRAME_LENGTH': data[Pms7003.PMS_FRAME_LENGTH],
                'PM1_0': data[Pms7003.PMS_PM1_0],
                'PM2_5': data[Pms7003.PMS_PM2_5],
                'PM10_0': data[Pms7003.PMS_PM10_0],
                'PM1_0_ATM': data[Pms7003.PMS_PM1_0_ATM],
                'PM2_5_ATM': data[Pms7003.PMS_PM2_5_ATM],
                'PM10_0_ATM': data[Pms7003.PMS_PM10_0_ATM],
                'PCNT_0_3': data[Pms7003.PMS_PCNT_0_3],
                'PCNT_0_5': data[Pms7003.PMS_PCNT_0_5],
                'PCNT_1_0': data[Pms7003.PMS_PCNT_1_0],
                'PCNT_2_5': data[Pms7003.PMS_PCNT_2_5],
                'PCNT_5_0': data[Pms7003.PMS_PCNT_5_0],
                'PCNT_10_0': data[Pms7003.PMS_PCNT_10_0],
                'VERSION': data[Pms7003.PMS_VERSION],
                'ERROR': data[Pms7003.PMS_ERROR],
                'CHECKSUM': data[Pms7003.PMS_CHECKSUM],
            }
