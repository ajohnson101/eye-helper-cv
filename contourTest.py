# -*- coding: utf-8 -*-
"""
Created on Wed Jun 11 14:34:59 2014

@author: koenigin
"""

import numpy as np
import cv2

cap = cv2.VideoCapture(0)

while(True):
    im = cap.read()[1]
    imgray = cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(imgray,127,255,0)
    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(im, contours, -1, (0,255,0), 3)
    cv2.imshow("window title", im)
    if cv2.waitKey(1) & 0xFF == ord('q'): #hit escape or the q key to end the loop
        break

#when everything's done, release the capture
cap.release()
cv2.destroyAllWindows()
