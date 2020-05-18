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


img_socks = [
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
]

img_socks[0].bind(("0.0.0.0", IMAGE_PORT))

cv.namedWindow('amap')
cv.moveWindow('amap', 0, 0)


rx_jpgs = [
    {'size': 0, 'packets': [], 'inBand': False},
    {'size': 0, 'packets': [], 'inBand': False},
    {'size': 0, 'packets': [], 'inBand': False},
]

images = [
    np.empty((480, 848, 3), np.uint8),
    np.empty((480, 848, 3), np.uint8),
    np.empty((480, 848, 3), np.uint8),
]

rx_data = [
    {
        'remote_id': 0,
        'nboxes': 0,
        'closestIdx': -1,
        'distances': np.zeros(16, np.float),
        'bboxes': np.zeros((16, 4), np.int32),
        'ts': time.time()
    },
    {
        'remote_id': 0,
        'nboxes': 0,
        'closestIdx': -1,
        'distances': np.zeros(16, np.float),
        'bboxes': np.zeros((16, 4), np.int32),
        'ts': time.time()
    },
    {
        'remote_id': 0,
        'nboxes': 0,
        'closestIdx': -1,
        'distances': np.zeros(16, np.float),
        'bboxes': np.zeros((16, 4), np.int32),
        'ts': time.time()
    },
]

nboxes = 0
distances = np.empty(16, np.float)
bboxes = np.empty((16,4), np.int32)



def rx_bbox_data(camNum, data, addr):
    rx_data[camNum]['remote_id'] = data[2]
    rx_data[camNum]['nboxes'] = min(16, data[3])
    rx_data[camNum]['ts'] = time.time()
    nboxes = min(16, data[3])
    for i in range(nboxes):
        iStart = i*20 + 4
        iStop = iStart + 20
        #distances[i], bboxes[i][0], bboxes[i][1], bboxes[i][2], bboxes[i][3] = \
        a, b, c, d, e = struct.unpack('fiiii', data[iStart:iStop])
        rx_data[camNum]['distances'][i] = a
        rx_data[camNum]['bboxes'][i][0] = b
        rx_data[camNum]['bboxes'][i][1] = c
        rx_data[camNum]['bboxes'][i][2] = d
        rx_data[camNum]['bboxes'][i][3] = e
    #if nboxes:
    #    print('nboxes:', nboxes)


def draw_bboxes(camNum):
    nboxes = rx_data[camNum]['nboxes']
    bboxes = rx_data[camNum]['bboxes']
    im = images[camNum]
    for i in range(nboxes):
        dst = rx_data[camNum]['distances'][i]
        bbox = rx_data[camNum]['bboxes'][i]
        if dst < STOP_DISTANCE:
            cimg2 = cv.rectangle(im, (bbox[0], bbox[2]), (bbox[1], bbox[3]),
                (0,0,255), 4)
        elif distances[i] < WARN_DISTANCE:
            cimg2 = cv.rectangle(im, (bbox[0], bbox[2]), (bbox[1], bbox[3]),
                (0,255,255), 4)
        else:
            cimg2 = cv.rectangle(im, (bbox[0], bbox[2]), (bbox[1], bbox[3]),
                (255,255,255), 3)

    if nboxes:
        closestIdx = np.argmin(rx_data[camNum]['distances'][:nboxes])
        closest_distance = np.min(rx_data[camNum]['distances'][:nboxes])

        font = cv.FONT_HERSHEY_SIMPLEX
        #if closest_distance < WARN_DISTANCE:
        #    text = "%.02f m" % (closest_distance)
        #    cv.putText(im, text, (19,119), font, 4, (0,0,0), 8)  # black shadow
        #    cv.putText(im, text, (10,110), font, 4, (255,255,255), 8)  # white text



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
                            #draw_bboxes(camNum)
                            maybe_render()
                else:
                    print('image size doesn\'t match')
        else:
            rx_jpgs[camNum]['packets'].append(data)
        
    #else:
    if True:
        if data.startswith(START_MAGIC):
            rx_jpgs[camNum]['size'] = int(data[-10:], 10)
            rx_jpgs[camNum]['packets'] = []
            rx_jpgs[camNum]['inBand'] = True



while True:
    inputs, outputs, errors = select.select(img_socks, [], [])
    for oneInput in inputs:
        if oneInput == img_socks[0]:
            imgdata, addr = img_socks[0].recvfrom(2048)
            rx_png_packet(0, imgdata, addr)


