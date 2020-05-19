
import numpy as np
import cv2

#from misc_utils import get_last_packet
from misc_map_tools import make_map
from VelodyneVLP16 import VelodyneVLP16, LOOKUP_COS, LOOKUP_SIN



class Visualizer(VelodyneVLP16):
    def __init__(self, do_gui=True, do_network=False):
        super(Visualizer, self).__init__()
        self.callback = self._callback
        height = 800
        width = 1400
        self._x_center = int(round(width / 2.0))
        #self._y_center = int(round(height / 2.0))
        self._y_center = 800 # offset at bottom of screen
        self._spacing = 100  # pixels per meter

        self._DO_GUI = do_gui
        self._DO_NETWORK = do_network
        self._X_MIN = 1
        self._Y_MIN = 1
        self._X_MAX = (width - 2)
        self._Y_MAX = (height - 2)

        self._a_map = make_map(width, height, self._spacing)
        self._map = np.copy(self._a_map)

        # Jet colormap, BGR:
        self._Laser_Colors = [
            (  0,   0, 255),
            (  0,  99, 255),
            (  0, 200, 255),
            ( 22, 255, 225),
            (125, 255, 122),
            (228, 252,  19),
            (255, 124,   0),
            (255,   0,   0),
        ]


        cv2.circle(self._map, (400, 400), 3, (120,64,0), 2)
        #self._map = np.copy(self.__map)

    def make_avoidance_areas(speed=0.0):
        l_scaling = 1.0 + 0.2* (speed-0.5)
        if l_scaling < 1.0:
            l_scaling = 1.0
        #elif l_scaling > 4.0:
        #    l_scaling = 4.0

        w_scaling = 1.0 + 0.02* (speed-0.5)
        if w_scaling < 1.0:
            w_scaling = 1.0
        elif w_scaling > 1.75:
            w_scaling = 1.75

        yy_scaling = 1.0 + 0.1* (speed-0.5)
        if yy_scaling < 1.0:
            yy_scaling = 1.0
        elif yy_scaling > 1.75:
            yy_scaling = 1.75

        amap = np.copy(_a_map)

        y_top_vert = int(round(800 - 400 * l_scaling))
        y_mid_vert = int(round(800 - 200 * l_scaling))
        if y_mid_vert < 400:
            y_mid_vert = 400
        y_left = int(round(700 - 200 * yy_scaling))
        y_right = int(round(700 + 200 * yy_scaling))

        y_pts = np.array([
            [600, 800],
            [y_left, y_mid_vert],
            [y_left, y_top_vert],
            [y_right, y_top_vert],
            [y_right, y_mid_vert],
            [800, 800]
        ], np.int32)
        y_pts.reshape((-1, 1, 2))
        cv.fillPoly(amap, [y_pts], (153, 255,255))

        cv.fillPoly(amap, [y_pts], (153, 255,255))

        # Red, "hard-turn" area:
        #r_w = int(round(100*w_scaling))
        #r_h = int(round(250*l_scaling))
        #cv.ellipse(amap, (700, 800), (r_w, r_h), 0, 0, -180, (153,153,255), -1)

        # Black, "Stop" area:
        k_w = int(round(80*w_scaling))
        k_h = int(round(100*l_scaling))
        #if k_h > 250:
        #    k_h = 250
        cv.ellipse(amap, (700, 800), (k_w, k_h), 0, 0, -180, (50, 50, 50), -1)

        return amap

    def _callback(self):

        #params = [cv2.IMWRITE_PNG_COMPRESSION, 1]
        params = [cv2.IMWRITE_JPEG_QUALITY, 20]
        if self._DO_NETWORK:
            _nothing, pngBuffer = cv2.imencode('*.jpg', self._map, params)
            bufLen = len(pngBuffer)
            filepos = 0
            numbytes = 0
            START_MAGIC = b"__HylPnaJY_START_PNG %09d\n" % (bufLen)
            lidar_sock.sendto(START_MAGIC, IMG_RECV_ADDRESS)
            while filepos < bufLen:
                if (bufLen - filepos) < 1400:
                    numbytes = bufLen - filepos
                else:
                    numbytes = 1400  # ethernet MTU is 1500
                lidar_sock.sendto(pngBuffer[filepos:(filepos+numbytes)], IMG_RECV_ADDRESS)
                filepos += numbytes
            STOP_MAGIC = b"_g1nC_EOF"
            lidar_sock.sendto(STOP_MAGIC, IMG_RECV_ADDRESS)


        for theta_min, theta_max in self.ppl_angles:

            # - Zero degrees points forward.
            # - positive angles are to the right (clockwise)
            # - negative angles are to the left (counter-clockwise)

            # But in the array, there is a "seam" at zero degrees

            idx_min = int(round(theta_min)) % 360
            idx_max = int(round(theta_max)) % 360

            if idx_max > idx_min:
                # contiguous range, treat as normal
                idx = np.argmin(self.ranges[idx_min:idx_max]) + idx_min
            else:
                # dis-contiguous range, must to multiple operations:
                idx1 = np.argmin(self.ranges[idx_min:]) + idx_min
                idx2 = np.argmin(self.ranges[:idx_max+1])
                if self.ranges[idx1] < self.ranges[idx2]:
                    idx = idx1
                else:
                    idx = idx2

            r = self.ranges[idx]
            if r > 0.01:
                x = r * np.sin(np.radians(idx))
                y = r * np.cos(np.radians(idx))
                x_px = self._x_center + int(np.round(x * self._spacing))
                y_px = self._y_center - int(np.round(y * self._spacing))

                #y = int(round(800 + 100 * np.cos(np.radians(idx)) * dist))
                #x = int(round(700 + 100 * np.sin(np.radians(idx)) * dist))
                if x_px > self._X_MIN and x_px < self._X_MAX:
                    if y_px > self._Y_MIN and y_px < self._Y_MAX:
                        #theta = 0.5 * (theta_min + theta_max)
                        #ppl_global_coords.append((dist, theta, x, y))
                        cv2.circle(self._map, (x_px,y_px), 11, [0,0,255], -1)
                        cv2.circle(self._map, (x_px,y_px), 13, [0,0,0], 2)


        if self._DO_GUI:
            cv2.imshow('asdf', self._map)
            cv2.waitKey(1)
        #if self._WRITE_VIDEO:
        #    vid_out.write(self._map)

        #self._map = self.make_avoidance_areas(speed=self.robot_speed)
        self._map = np.copy(self._a_map)


