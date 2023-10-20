"""
Implementation of the Multicast DNS and DNS-Based Service Discovery protocols.

References
----------
* RFC-1035_ -- *Domain Names - Implementation and Specification*, **ISI**, November 1987.
* RFC-6762_ -- *Multicast DNS*, **Apple Inc.**, February 2013.
* RFC-6763_ -- *DNS-Based Service Discovery*, **Apple Inc.**, February 2013.

.. _RFC-1035: https://www.rfc-editor.org/rfc/rfc1035
.. _RFC-6762: https://www.rfc-editor.org/rfc/rfc6762
.. _RFC-6763: https://www.rfc-editor.org/rfc/rfc6763
"""
from __future__ import annotations

import socket
import struct
import threading
import time

import select

from .utils import parse_lxi_webserver

# RFC 6762, Section 5.1
MDNS_ADDR = '224.0.0.251'
MDNS_ADDR6 = 'ff02::fb'
MDNS_PORT = 5353

# RFC 1035, Section 3.2.2
A = 1  # a host address
PTR = 12  # a domain name pointer
TXT = 16  # text strings

# RFC 2782, Page 2
SRV = 33  # location of services

# RFC 1035, Section 3.2.4
IN = 1  # the internet


class _Buffer(object):

    def __init__(self, data):
        self.data = data
        self.offset = 0

    def get(self, length):
        start = self.offset
        self.offset += length
        return self.data[start:start + length]

    def unpack(self, fmt):
        size = struct.calcsize(fmt)
        return struct.unpack(fmt, self.get(size))

    def decode_name(self):
        # RFC 1035, Section 4.1.2
        # a domain name represented as a sequence of labels, where
        # each label consists of a length octet followed by that
        # number of octets. The domain name terminates with the
        # zero length octet for the null label of the root.
        names = []
        while True:
            length, = self.unpack('!B')
            if length == 0:
                names.append('')
                break
            elif length & 0b11000000:
                # RFC 1035, Section 4.1.4 (Pointer)
                self.offset -= 1
                pointer = self.unpack('!H')[0] & 0b0011111111111111
                offset = self.offset
                self.offset = pointer
                names.extend(self.decode_name())
                self.offset = offset
                break
            else:
                names.append(self.get(length).decode())
        return names


class _DNSRecord(_Buffer):

    def __init__(self, reply):
        super(_DNSRecord, self).__init__(reply)

        # RFC 1035, Section 4.1.1
        tid, flags, qd_count, an_count, ns_count, ar_count = self.unpack('!6H')
        assert tid == 0  # get the same transaction identifier back
        assert flags & 0b1000010000000000  # QR=1, OPCODE=0, AA=1, TC=0, RD=0, RA=0, Z=0, RCODE=0

        self.questions = [self.parse_question() for _ in range(qd_count)]
        self.answers = [self.parse_resource_record() for _ in range(an_count)]
        self.authority = [self.parse_resource_record() for _ in range(ns_count)]
        self.additional = [self.parse_resource_record() for _ in range(ar_count)]

    def parse_question(self):
        # RFC 1035, Section 4.1.2
        q_name = '.'.join(self.decode_name())
        q_type, q_class = self.unpack('!2H')
        return {'name': q_name, 'type': q_type, 'class': q_class}

    def parse_resource_record(self):
        # RFC 1035, Section 4.1.3
        r_name = '.'.join(self.decode_name())
        r_type, r_class, ttl, rd_length = self.unpack('!2HIH')
        if rd_length == 0:
            r_data = None
        elif r_type == PTR:
            # RFC 1035, Section 3.3.12
            r_data = '.'.join(self.decode_name())
        elif r_type == SRV:
            # RFC 2782
            priority, weight, port = self.unpack('!3H')
            r_data = {
                'priority': priority,
                'weight': weight,
                'port': port,
                'target': '.'.join(self.decode_name())
            }
        elif r_type == TXT:
            # RFC 1035, Section 3.3.14
            txt_data = []
            stop = self.offset + rd_length
            while self.offset < stop:
                txt_length, = self.unpack('!B')
                txt_data.append(self.get(txt_length).decode())

            # LXI Device Specification 2022 (Revision 1.6), Section 10.4.3
            r_data = dict(item.split('=') for item in txt_data)
        elif r_type == A:
            # RFC 1035, Section 3.4.1
            r_data = self.unpack('!4B')
        else:
            r_data = self.get(rd_length)
        return {'name': r_name, 'type': r_type, 'class': r_class, 'ttl': ttl, 'data': r_data}


def find_lxi(hosts=None, timeout=1):
    """Find all LXI devices that support the mDNS and DNS Service Discovery protocols.

    Parameters
    ----------
    hosts : :class:`list` of :class:`str`, optional
        The IP address(es) on the computer to use to broadcast the message.
        If not specified, then broadcast on all network interfaces.
    timeout : :class:`float`, optional
        The maximum number of seconds to wait for a reply.

    Returns
    -------
    :class:`dict`
        The information about the HiSLIP, VXI-11 and SCPI-RAW devices
        that were found.
    """
    if not hosts:
        from .utils import ipv4_addresses
        all_ips = ipv4_addresses()
    else:
        all_ips = hosts

    services = [
        # VXI-11 Discovery and Identification Extended Function (Revision 1.1), Section 10.1.5
        b'_vxi-11._tcp.local.',

        # LXI HiSLIP Extended Function (Revision 1.3), Section 20.7.1
        b'_hislip._tcp.local.',

        # LXI Device Specification 2022 (Revision 1.6), Section 10.4.3
        b'_http._tcp.local.',
        b'_lxi._tcp.local.',
        b'_scpi-raw._tcp.local.',
        b'_scpi-telnet._tcp.local.'
    ]

    # RFC 1035, Section 4
    id_ = 0  # transaction identifier
    flags = 0  # QR=0, OPCODE=0, AA=0, TC=0, RD=0, RA=0, Z=0, RCODE=0
    qd_count = len(services)  # the number of Questions
    an_count = 0  # No Resource Records in the Answer section
    ns_count = 0  # No Name Server Resource Records in the Authority Records section
    ar_count = 0  # No Resource Records in the Additional Records section
    header = struct.pack('!6H', id_, flags, qd_count, an_count, ns_count, ar_count)

    # Initialize the DNS message
    message = bytearray(header)

    # Add the Questions to the DNS message
    for service in services:
        for name in service.split(b'.'):
            message.extend(struct.pack('!B', len(name)))
            message.extend(name)
        message.extend(struct.pack('!2H', PTR, IN))

    def parse_xml(ip_address, port=80):
        try:
            lxi = parse_lxi_webserver(ip_address, port=port, timeout=timeout)
        except:
            return {}, set()

        description = {
            'Manufacturer': lxi.get('Manufacturer', 'Unknown'),
            'Model': lxi.get('Model', 'Unknown'),
            'SerialNumber': lxi.get('SerialNumber', 'Unknown'),
            'ManufacturerDescription': lxi.get('ManufacturerDescription', lxi.get('title', 'Unknown')),
        }

        addresses = set()
        for interface in lxi.get('Interfaces', []):
            if interface['InterfaceType'] != 'LXI':
                continue
            for address in interface['InstrumentAddressStrings']:
                addresses.add(address)
        return description, addresses

    def discover(host):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        sock.bind((host, 0))
        sock.sendto(message, (MDNS_ADDR, MDNS_PORT))
        select_timeout = min(timeout*0.1, 0.1)
        t0 = time.time()
        while True:
            r, w, x = select.select([sock], [], [], select_timeout)
            if time.time() - t0 > timeout:
                break
            if not r:
                continue

            reply, (ip_address, _) = sock.recvfrom(8192)
            try:
                record = _DNSRecord(reply)
            except:
                continue

            device = {}
            info = {}
            addresses = set()
            found_lxi_srv = False

            # Check SRV and TXT records
            for a in record.additional:
                if a['type'] == TXT:
                    info.update(a['data'])
                elif a['type'] == SRV:
                    port = a['data']['port']
                    if a['name'].endswith('_scpi-raw._tcp.local.'):
                        addresses.add('TCPIP::{}::{}::SOCKET'.format(ip_address, port))
                    elif a['name'].endswith('_vxi-11._tcp.local.'):
                        port_str = '' if port == 111 else ',{}'.format(port)
                        addresses.add('TCPIP::{}::inst0{}::INSTR'.format(ip_address, port_str))
                    elif a['name'].endswith('_hislip._tcp.local.'):
                        port_str = '' if port == 4880 else ',{}'.format(port)
                        addresses.add('TCPIP::{}::hislip0{}::INSTR'.format(ip_address, port_str))
                    elif a['name'].endswith('_lxi._tcp.local.'):
                        found_lxi_srv = True
                        port_str = '' if port == 80 else ':{}'.format(port)
                        device['webserver'] = 'http://{}{}'.format(ip_address, port_str)
                        description, address_strings = parse_xml(ip_address, port=port)
                        info.update(description)
                        for item in address_strings:
                            addresses.add(item)

            # Fetch the XML identification document (if it hasn't already been fetched)
            if not found_lxi_srv:
                for a in record.answers:
                    if a['name'] in ('_lxi._tcp.local.', '_http._tcp.local.'):
                        description, address_strings = parse_xml(ip_address)
                        device['webserver'] = 'http://{}'.format(ip_address)
                        info.update(description)
                        for item in address_strings:
                            addresses.add(item)

            md = info.get('ManufacturerDescription', '')
            description = []
            for item in ('Manufacturer', 'Model', 'SerialNumber'):
                if item in info and info[item] not in md:
                    description.append(info[item])
            if md:
                description.append(md)

            if description:
                device['description'] = ', '.join(description)
            else:
                device['description'] = 'Unknown LXI device'

            device['addresses'] = sorted(addresses)

            key = tuple(int(s) for s in ip_address.split('.'))
            devices[key] = device

        sock.close()

    # TODO use asyncio instead of threading when dropping Python 2.7 support

    devices = {}
    threads = [threading.Thread(target=discover, args=(ip,)) for ip in all_ips]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return dict((k, devices[k]) for k in sorted(devices))
