#!/usr/bin/env python3
  
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

import os
import time
import select
import socket
import struct
import numpy as np
import cv2

from misc_utils import get_last_packet
from misc_map_tools import make_map


from BBox_Parser import BBox_Parser
from Visualizer import Visualizer


VELODYNE_PORT = 2368
lidar_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
lidar_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
lidar_sock.bind(("0.0.0.0", VELODYNE_PORT))


# This is lat,lon,heading,speed from "LocationServices":
NAV_PORT = 27201
nav_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
nav_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
nav_sock.bind(("127.0.0.1", NAV_PORT))


#WRITE_VIDEO = False
#vid_out = None
#if len(sys.argv) > 1:
#    WRITE_VIDEO = True
#    filename = sys.argv[1]
#    vid_out = cv2.VideoWriter('cam_video.mjpg', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (800, 800))

DO_NETWORK = False
IMG_RECV_ADDRESS = ('127.0.0.1', 53521)

FOLLOW_AVOID_RECV_ADDRESS = ('127.0.0.1', 52535)
DO_GUI = True

myVis = Visualizer(FOLLOW_AVOID_RECV_ADDRESS, do_gui=True, do_network=False)
bboxParser = BBox_Parser()


BBOX_PORT = 4101 # 3101
bbox_socks = [
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
]
bbox_socks[0].bind(("0.0.0.0", BBOX_PORT))
bbox_socks[1].bind(("0.0.0.0", BBOX_PORT + 1))
bbox_socks[2].bind(("0.0.0.0", BBOX_PORT + 2))


all_sockets = [lidar_sock, nav_sock] + bbox_socks

while True:
    inputs, outputs, errors = select.select(all_sockets, [], [])
    for oneInput in inputs:
        if oneInput == lidar_sock:
            #pkt, addr = lidar_sock.recvfrom(2048)
            pkt, addr = get_last_packet(lidar_sock, 2048, verbose=False)

            myVis.parse_UDP_packet(pkt)


        elif oneInput == bbox_socks[0]:
            bboxParser.rx_packet(0, bbox_socks[0])
            myVis.ppl_angles = bboxParser.get_all_ppl_angles()

        elif oneInput == bbox_socks[1]:
            bboxParser.rx_packet(1, bbox_socks[1])
            myVis.ppl_angles = bboxParser.get_all_ppl_angles()

        elif oneInput == bbox_socks[2]:
            bboxParser.rx_packet(2, bbox_socks[2])
            myVis.ppl_angles = bboxParser.get_all_ppl_angles()

        elif oneInput == nav_sock:
            #pkt, addr = nav_sock.recvfrom(32)
            pkt, addr = get_last_packet(nav_sock, 32, verbose=False)
            try:
                lat, lon, hdg, _current_spd = struct.unpack('!dddd', pkt)
            except Exception as ee:
                print('failed to parse location packet:', ee)
            else:
                pass
                #speedControl.set_actual(_current_spd)



