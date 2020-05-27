#!/usr/bin/env python3

import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")


import os
import select
import socket
import struct
import time
import numpy as np
import cv2 as cv



WRITE_VIDEO = False
vid_out = None

if len(sys.argv) == 2:
    WRITE_VIDEO = True
    vid_filename = sys.argv[1]

if WRITE_VIDEO:
    vid_out = cv.VideoWriter(vid_filename, cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 20, (2544, 480))


START_MAGIC = b"__HylPnaJY_START_PNG "
STOP_MAGIC = b"_g1nC_EOF"

IMAGE_PORT = 53521


img_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
img_sock.bind(("0.0.0.0", IMAGE_PORT))

cv.namedWindow('amap')
cv.moveWindow('amap', 0, 0)


rx_jpgs = [
    {'size': 0, 'packets': [], 'inBand': False},
]

images = [
    np.empty((480, 848, 3), np.uint8),
]



_last_render_time = time.time()
def maybe_render():
    global _last_render_time
    t1 = time.time()
    tDelta = t1 - _last_render_time
    if tDelta > 0.05:
        _last_render_time = t1
        #frame = np.hstack(images)
        cv.imshow('amap', images[0])
        cv.waitKey(1)
        if WRITE_VIDEO:
            vid_out.write(frame)


def rx_png_packet(camNum, data, addr):
    global rx_jpgs
    global images
    if rx_jpgs[camNum]['inBand']:
        if data == STOP_MAGIC:
            rx_jpgs[camNum]['inBand'] = False
            if len(rx_jpgs[camNum]['packets']) > 1:
                jpgData = b''.join(rx_jpgs[camNum]['packets'])
                if rx_jpgs[camNum]['size'] == len(jpgData):
                    rx_jpgs[camNum]['jpgData'] = np.frombuffer(jpgData, np.uint8)
                    try:
                        im = cv.imdecode(rx_jpgs[camNum]['jpgData'], cv.IMREAD_UNCHANGED)
                    except Exception as ee:
                        print("Failed to decode jpeg:", ee)
                    else:
                        if im is not None:
                            images[camNum] = im
                            maybe_render()
                else:
                    print('image size doesn\'t match')
        else:
            rx_jpgs[camNum]['packets'].append(data)
        
    if data.startswith(START_MAGIC):
        rx_jpgs[camNum]['size'] = int(data[-10:], 10)
        rx_jpgs[camNum]['packets'] = []
        rx_jpgs[camNum]['inBand'] = True



while True:
    inputs, outputs, errors = select.select([img_sock], [], [])
    for oneInput in inputs:
        if oneInput == img_sock:
            imgdata, addr = img_sock.recvfrom(2048)
            rx_png_packet(0, imgdata, addr)


