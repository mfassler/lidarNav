
import math
import struct
import numpy as np


LOOKUP_COS = np.empty(36000)
LOOKUP_SIN = np.empty(36000)
for i in range(36000):
    LOOKUP_COS[i] = np.cos(np.radians(i/100.0))
    LOOKUP_SIN[i] = np.sin(np.radians(i/100.0))


def _nothing_function_(_self_):
    pass


class VelodyneVLP16:
    def __init__(self):
        self.callback = _nothing_function_
        self._prev_azimuth = 0
        #self._count = 0
        self.ranges = np.zeros(360)
        self.ppl_angles = []
        self.max_azi = 5000
        self.min_azi = 5000

    def parse_data_block(self, data_block):
        flag, azimuth = struct.unpack('HH', data_block[:4])

        if azimuth > self.max_azi:
            self.max_azi = azimuth
        elif azimuth < self.min_azi:
            self.min_azi = azimuth

        # this puts the "seam" in the front
        #if azimuth < self._prev_azimuth:

        # this puts the "seam" in the back (by the cable)
        if self._prev_azimuth < 13500 and azimuth >= 13500:
            self.callback()
            #print(self._count)
            #self._prev_azimuth = 0
            #self._count = 0

        d_azimuth = (azimuth - self._prev_azimuth) % 36000
        #self._d_azimuth_history.append(d_azimuth)

        self._prev_azimuth = azimuth

        dist, = struct.unpack('H', data_block[7:9])
        if dist == 0:
            return

        #self._count += 1
        r = 0.002 * dist

        # ranges is 360 slots, 1 per degree
        # rotate 180 degrees so that 0 degrees is in the middle
        idx = math.floor(azimuth / 100.0)
        self.ranges[idx] = r

        x = r * LOOKUP_SIN[azimuth]
        y = r * LOOKUP_COS[azimuth]

        x_px = self._x_center + int(np.round(x * self._spacing))
        y_px = self._y_center - int(np.round(y * self._spacing))
        if x_px > self._X_MIN and x_px < self._X_MAX and y_px > self._Y_MIN and y_px < self._Y_MAX:
            self._map[y_px, x_px] = (0,0,0)
            self._map[y_px+1, x_px] = (0,0,0)
            self._map[y_px, x_px+1] = (0,0,0)
            self._map[y_px+1, x_px+1] = (0,0,0)


    def parse_UDP_packet(self, pkt):
        if len(pkt) == 1206:
            ts, fac = struct.unpack('IH', pkt[-6:])
            for i in range(12):
                iStart = i*100
                iStop = iStart + 100
                data_block = pkt[iStart:iStop]
                self.parse_data_block(data_block)
        else:
            print('Velodyne packet wrong size!')

