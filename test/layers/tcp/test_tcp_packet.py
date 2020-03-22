from unittest import TestCase

from port_scanner.layers.ip.ip_packet import IpPacket
from port_scanner.layers.tcp.tcp_packet import TcpPacket
from port_scanner.layers.tcp.tcp_control_bits import TcpControlBits
from port_scanner.layers.tcp.tcp_options import TcpOptions

#
# Source port = 59700
# Destination port = 443
# Sequence number = 1407506493
# Acknowledgment number = 3676709599
# Flags = 0x010 (ACK)
# Window size = 501
# Checksum = 0x9156
# Urgent pointer = 0
# Options:
#   NOP
#   NOP
#   Timestamps = 3252488245 and 365238493
#
# Underlying IP:
#   Src = 192.168.1.32
#   Dst = 35.160.240.60
#

PACKET_DUMP_1 = "e93401bb53e4d83ddb2622df801001f5915600000101080ac1dd083515c518dd"


class TestTcpPacket(TestCase):

    def test_to_bytes(self):
        tcp_options = TcpOptions([
            TcpOptions.NOP,
            TcpOptions.NOP,
            (TcpOptions.TIMESTAMPS, [3252488245, 365238493])
        ])

        tcp_packet = TcpPacket(
            source_port=59700,
            dest_port=443,
            sequence_number=1407506493,
            ack_number=3676709599,
            flags=TcpControlBits(ack=True),
            win_size=501,
            urg_pointer=0,
            options=tcp_options,
            payload=bytearray(0)
        )

        ip_packet = IpPacket(
            source_addr_str="192.168.1.32",
            dest_addr_str="35.160.240.60"
        )

        tcp_packet.underlying_packet = ip_packet

        self.assertEqual(PACKET_DUMP_1, tcp_packet.to_bytes().hex())

    def test_copy(self):
        tcp_packet = TcpPacket(
            source_port=59700,
            dest_port=443,
            sequence_number=1407506493,
            ack_number=3676709599,
            flags=TcpControlBits(ack=True),
            win_size=501,
            urg_pointer=0,
            options=TcpOptions([
                TcpOptions.NOP,
                TcpOptions.NOP,
                (TcpOptions.TIMESTAMPS, [3252488245, 365238493])
            ]),
            payload=bytearray(0)
        )
        self.assertEqual(tcp_packet, tcp_packet.clone())
