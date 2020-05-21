#!/usr/bin/env python3

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import struct
import socket
import select

FOLLOW_AVOID_PORT = 52535
fa_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
fa_sock.bind(('0.0.0.0', FOLLOW_AVOID_PORT))



class FollowAvoid:
    def __init__(self):
        self.follow_r = 100.0
        self.follow_angle = 0.0
        self.avoid_color = b' '
        self.avoid_x = 0.0   # meters, left is negative, right is positive
        self.avoid_y = 0.0   # meters, how far in front of robot
        self.PACKET_SIZE = struct.calcsize(b'ddddcbbb')

    def parse_packet(self, pkt):
        ap_lr, ap_langle, ap_avx, ap_avy, ap_avColor, _n1, _n2, _n3 = struct.unpack(b'ddddcbbb', pkt)
        self.follow_r = ap_lr
        self.follow_angle = ap_langle
        self.avoid_color = ap_avColor
        self.avoid_x = ap_avx
        self.avoid_y = ap_avy

    def printSelf(self):
        print("%.02f %.02f   - %s %.02f %.02f" % (self.follow_r, self.follow_angle, self.avoid_color, self.avoid_x, self.avoid_y))


folAvoid = FollowAvoid()

while True:
    inputs, outputs, errors = select.select([fa_sock], [], [])

    for oneInput in inputs:
        #pkt, addr = get_last_packet(fa_sock, 512)
        pkt, addr = fa_sock.recvfrom(512)
        if len(pkt) != folAvoid.PACKET_SIZE:
            print('follow_avoid UDP packet wrong size')
        else:
            try:
                folAvoid.parse_packet(pkt)
            except Exception as ee:
                print('folAvoid failed:', ee)
            else:
                folAvoid.printSelf()




