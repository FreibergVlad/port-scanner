import socket
from unittest import TestCase
from port_scanner.layers.ip.ip_packet import IpPacket

"""
Hex dump of IP packet with the following properties:
    DSCP = 0
    total length = 393 bytes (20 + 373)
    identification = 31205
    flags = 0x4000
    ttl = 252
    protocol = TCP (6)
    source IP = 93.186.225.198
    destination IP = 192.168.1.16
"""
HEX_DUMP_1 = "4500018979e54000fc0602505dbae1c6c0a80110"

"""
Hex dump of IP packet with the following properties:
    DSCP = 0
    total length = 68 bytes (20 + 48)
    identification = 27536
    flags = 0x4000
    ttl = 64
    protocol = UDP (17)
    source IP = 192.168.0.102
    destination IP = 192.168.0.1
"""
HEX_DUMP_2 = "450000446b90400040114d61c0a80066c0a80001"


class TestIpv4Packet(TestCase):

    def test_pack(self):
        ip_packet_1 = IpPacket(
            source_addr_str="93.186.225.198",
            dest_addr_str="192.168.1.16",
            payload=bytearray(373),
            ttl=252,
            identification=31205
        )
        hex_dump_1 = ip_packet_1.pack().hex()
        self.assertEqual(HEX_DUMP_1, hex_dump_1)

        ip_packet_2 = IpPacket(
            source_addr_str="192.168.0.102",
            dest_addr_str="192.168.0.1",
            payload=bytearray(48),
            ttl=64,
            identification=27536,
            protocol=socket.IPPROTO_UDP
        )
        hex_dump_2 = ip_packet_2.pack().hex()
        self.assertEqual(HEX_DUMP_2, hex_dump_2)