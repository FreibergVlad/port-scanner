class Utils:

    @staticmethod
    def set_bit(num: int, bit_mask: int, value: bool) -> int:
        if value:  # bit is 1
            return num | bit_mask
        else:  # bit is 0
            return num & ~bit_mask

    @staticmethod
    def is_bit_set(bits: int, bit_mask: int) -> bool:
        return bits & bit_mask != 0

    @staticmethod
    def calc_checksum(byte_buffer: bytearray) -> int:
        """
        Calculates checksum, the following algorithm is applied for IPv4, TCP, UDP protocols:
            - Split input byte sequence to 16 bits words
            - Compute sum of these words
            - Compute sum one's complement
        :param: byte_buffer: input byte sequence
        :return: calculated checksum (16 bits value)
        """
        checksum = 0
        for i in range(0, len(byte_buffer), 2):
            # pair two bytes into 16-bits value
            paired_bytes = (byte_buffer[i] << 8) + byte_buffer[i + 1]
            checksum += paired_bytes
        checksum += (checksum >> 16)
        checksum = ~checksum & 0xffff
        return checksum
