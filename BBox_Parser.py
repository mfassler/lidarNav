
import time
import struct

from misc_utils import get_last_packet



class BBox_Parser:
    def __init__(self):
        self.ppl_angles = [[],[],[]]
        self._last_updates = [time.time(), time.time(), time.time()]
        self._packets = []

    def rx_packet(self, camNum, sock):
        data, addr = get_last_packet(sock, 1500)
        remote_id = data[2]
        nboxes = min(16, data[3])
        if nboxes > 0:
            self._packets.append((camNum, data))
        _ppl_angles = []
        for i in range(nboxes):
            iStart = i*20 + 4
            iStop = iStart + 20
            dist_meters, x_min, x_max, y_min, y_max = struct.unpack('fiiii', data[iStart:iStop])
            x_pixel = int(round((x_min+x_max)/2.0))
            angle_min = 41.0* (x_min - 424) / 424.0
            angle_max = 41.0 * (x_max - 424) / 424.0

            # the 3 cameras are mounted at 60 degree angles to each other:
            if camNum == 0:  # left
                angle_min -= 72
                angle_max -= 66
            elif camNum == 2:  # right
                angle_min += 66
                angle_max += 72

            _ppl_angles.append((angle_min, angle_max))
        self.ppl_angles[camNum] = _ppl_angles
        self._last_updates[camNum] = time.time()

    def get_all_ppl_angles(self):
        return self.ppl_angles[0] + self.ppl_angles[1] + self.ppl_angles[2]

    def check(self):
        ts = time.time()
        for i in range(3):
            if ts - self._last_updates[i] > 0.5:
                self.ppl_angles[i] = []


