
import time
import numpy as np


class LockOn:
    def __init__(self):
        self.pos = np.array([0.0, 0.0])
        self.r = 0.0
        self.angle = 0.0
        self.ts = time.time()
        self.confidence = 0.0

    def calc_angles_and_distances(self):
        self.dist2lock = np.empty(len(self.ppl_global_coords))

        for i, row in enumerate(self.ppl_global_coords):
            _pos = np.array([row[2], row[3]])
            self.dist2lock[i] = np.linalg.norm(_pos - self.pos)

    def choose_target(self, ppl_global_coords):
        self.ppl_global_coords = ppl_global_coords
        self.calc_angles_and_distances()

        if self.confidence < 0.1:
            # lock on to the closest person who is within +/- 40 degrees:
            idx = None
            dist = 9999
            for i, row in enumerate(self.ppl_global_coords):
                r, angle, x, y = row
                if angle > -40.0 and angle < 40.0:
                    if r < 5.0 and r < dist:
                        idx = i
                        dist = r
            if idx is not None:
                self.r, self.angle, x, y = self.ppl_global_coords[idx]
                self.pos = np.array([x, y])
                self.confidence = 0.5
                self.calc_angles_and_distances()

        else:
            if len(self.dist2lock):
                if self.dist2lock.min() < 150:   # 100 pixels per meter
                    idx = self.dist2lock.argmin()
                    self.r, self.angle, x, y = self.ppl_global_coords[idx]
                    self.pos = np.array([x, y])
                    self.confidence = 0.8 * self.confidence + 0.2
                else:
                    self.confidence = 0.8 * self.confidence + 0.0
            else:
                self.confidence = 0.65 * self.confidence + 0.0

        #print("%.02f" % (self.confidence))


