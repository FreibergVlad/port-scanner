import struct

from port_scanner.layers.packet import Packet
from port_scanner.layers.transport.tcp.tcp_control_bits import TcpControlBits
from port_scanner.layers.transport.tcp.tcp_utils import TcpUtils
from port_scanner.layers.transport.tcp.tcp_options import TcpOptions
from port_scanner.layers.transport.transport_layer_utils import TransportLayerUtils
from port_scanner.utils.utils import Utils


class TcpPacket(Packet):
    """
    Represents TCP (Transmission Control Protocol) packet
    """

    TCP_HEADER_FORMAT = "!HHIIHHHH"
    """
    Defines TCP header format without options:
        * Source port field : 2 bytes
        * Destination port field : 2 bytes
        * Sequence number field : 4 bytes
        * Acknowledgment number field : 4 bytes
        * Data offset field + 3 reserved bits + 9 bit flags : 2 bytes
        * Window size field : 2 bytes
        * Checksum field : 2 bytes
        * Urgent pointer field : 2 bytes
    """

    def __init__(
            self,
            source_port: int,
            dest_port: int,
            sequence_number: int = 0,
            ack_number: int = 0,
            flags: TcpControlBits = TcpControlBits(),
            win_size: int = 65535,
            urg_pointer: int = 0,
            options: TcpOptions = TcpOptions(),
            payload: bytearray = bytearray()
    ):
        """
        Initializes TCP packet instance

        :param source_port: Source port field value, integer in range [0; 65535]
        :param dest_port: Destination port field value, integer in range [0; 65535]
        :param sequence_number: Sequence number field value. Has a dual role:
            If the SYN flag is set (1), then this is the initial sequence number.
                The sequence number of the actual first data byte and the acknowledged number
                in the corresponding ACK are then this sequence number plus 1.
            If the SYN flag is clear (0), then this is the accumulated sequence number of the
                first data byte of this segment for the current session.
        :param ack_number: Acknowledgment number field value. If the ACK flag is set then the
            value of this field is the next sequence number that the sender of the ACK is expecting.
            This acknowledges receipt of all prior bytes (if any). The first ACK sent by each end
            acknowledges the other end's initial sequence number itself, but no data.
        :param flags: Flags field. Instance of TcpControlBits class. Contains 9 1-bit flags (control bits)
        :param win_size: Window size field value. The size of the receive window, which specifies
            the number of window size units that the sender of this segment is currently willing to receive.
        :param urg_pointer: Urgent pointer field value. If the URG flag is set, then this 16-bit field
            is an offset from the sequence number indicating the last urgent data byte.
        :param options: Options field. Instance of TcpOptions class.
        :param payload: packet payload
        """
        super().__init__()
        self.__source_port = TransportLayerUtils.validate_port_num(source_port)
        self.__dest_port = TransportLayerUtils.validate_port_num(dest_port)
        self.__sequence_number = sequence_number
        self.__ack_number = ack_number
        self.__flags = flags
        self.__win_size = win_size
        self.__urg_pointer = urg_pointer
        self.__options = options
        self.__payload = payload

    def to_bytes(self):
        options_bytes = self.__options.to_bytes()
        # make sure that options bit length is divisible by 32
        # should not fail here since all required padding already performed in TcpOptions class
        assert len(options_bytes) % 4 == 0
        # calculate data offset value in 32-bits words
        data_offset = TcpUtils.TCP_HEADER_LENGTH + len(options_bytes) // 4
        # concat 4 data offset bits + 3 reserved zero bits + 9 control bit flags
        data_offset_flags = data_offset << 12 | self.__flags.flags

        header_fields = [
            self.__source_port,
            self.__dest_port,
            self.__sequence_number,
            self.__ack_number,
            data_offset_flags,
            self.__win_size,
            0,
            self.__urg_pointer,
        ]

        # allocate 20 bytes buffer to put header in
        header_buffer = bytearray(TcpUtils.TCP_HEADER_LENGTH_BYTES)
        # pack header without checksum to the buffer
        struct.pack_into(self.TCP_HEADER_FORMAT, header_buffer, 0, *header_fields)

        # generate pseudo header using underlying IP packet
        pseudo_header = TransportLayerUtils.get_pseudo_header(
            self,
            data_offset * 4 + len(self.__payload)
        )
        # calculate checksum
        checksum = Utils.calc_checksum(pseudo_header + header_buffer + options_bytes + self.__payload)
        # split 16-bits checksum into two 8-bits values
        checksum_bytes = checksum.to_bytes(2, byteorder="big")
        # checksum takes 16-th and 17-th bytes of the header (counting from 0)
        # see https://tools.ietf.org/html/rfc793#section-3.1 for more details
        header_buffer[16] = checksum_bytes[0]
        header_buffer[17] = checksum_bytes[1]

        return TransportLayerUtils.validate_packet_length(bytes(header_buffer) + options_bytes + self.__payload)

    @staticmethod
    def from_bytes(packet_bytes: bytes):
        header_bytes = packet_bytes[:TcpUtils.TCP_HEADER_LENGTH_BYTES]
        payload_and_options = packet_bytes[TcpUtils.TCP_HEADER_LENGTH_BYTES:]
        header_fields = struct.unpack(TcpPacket.TCP_HEADER_FORMAT, header_bytes)

        source_port = header_fields[0]
        dest_port = header_fields[1]
        seq_num = header_fields[2]
        ack_num = header_fields[3]
        data_offset_flags = header_fields[4]
        win_size = header_fields[5]
        # 6-th item is checksum, don't need to extract it, since it will be calculated later
        urg_pointer = header_fields[7]

        # take first 4 bits
        data_offset = data_offset_flags >> 12
        # take 5-th, 6-th, 7-th bits
        reserved_bits = (data_offset_flags >> 9) & 7
        if reserved_bits != 0:
            raise ValueError("Reserved bits should be set to zero")
        # take last 9 bits
        flags = TcpControlBits.from_int(data_offset_flags & 511)

        # compute options field length in bytes
        options_len = (data_offset - TcpUtils.TCP_HEADER_LENGTH) * 4
        options = TcpOptions.from_bytes(payload_and_options[:options_len])

        payload = payload_and_options[options_len:]

        return TcpPacket(
            dest_port=dest_port,
            source_port=source_port,
            sequence_number=seq_num,
            ack_number=ack_num,
            flags=flags,
            win_size=win_size,
            urg_pointer=urg_pointer,
            options=options,
            payload=payload
        )

    @property
    def source_port(self) -> int:
        return self.__source_port

    @property
    def dest_port(self) -> int:
        return self.__dest_port

    @property
    def sequence_number(self) -> int:
        return self.__sequence_number

    @property
    def ack_number(self) -> int:
        return self.__ack_number

    @property
    def flags(self) -> TcpControlBits:
        return self.__flags

    @property
    def win_size(self) -> int:
        return self.__win_size

    @property
    def urg_pointer(self) -> int:
        return self.__urg_pointer

    @property
    def options(self) -> TcpOptions:
        return self.__options

    @property
    def payload(self) -> bytearray:
        return self.__payload

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TcpPacket):
            return self.dest_port == other.dest_port and \
                   self.source_port == other.source_port and \
                   self.upper_layer == other.upper_layer and \
                   self.sequence_number == other.sequence_number and \
                   self.ack_number == other.ack_number and \
                   self.flags == other.flags and \
                   self.win_size == other.win_size and \
                   self.urg_pointer == other.urg_pointer and \
                   self.options == other.options and \
                   self.payload == other.payload

    def __str__(self) -> str:
        return f"TCP(dest_port={self.dest_port}, src_port={self.source_port}, " \
               f"seq_num={self.sequence_number}, ack_num={self.ack_number}, " \
               f"flags=({self.flags}), win_size={self.win_size}, urg_pointer={self.urg_pointer}, " \
               f"options=({self.options}))"
