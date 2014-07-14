import cv2
import numpy as np 


def match_object(previous, current, train_img):
    """
    Takes in:
        Corners of the previous image as a list [x, y, x2, y2]
        current image with path
    Outputs:


    """
    
    img = cv2.imread(current, 0) #opens correct image in greyscale
    t_img = cv2.imread(train_img, 0)
    #takes in the coreners of where the object was before and adds 
    #a tolerance 
    x = previous[0] -75
    y = previous[1] -75
    x2 = previous[2] +75
    y2 = previous[3] +75

    #crops image to reduce the neccessary search area
    crop_img = img[y:y2, x:x2] # NOTE: its img[y: y + h, x: x + w] and *not* img[x: x + w, y: y + h]

    detector = cv2.ORB()

    t_k, t_d = detector.detectAndCompute(t_img, None)         #training image
    q_k, q_d = detector.detectAndCompute(crop_img, None)      #query image

    matcher = cv2.BFMatcher(normType = cv2.NORM_HAMMING)
    matches = matcher.knnMatch(q_d, t_d, k =2)

    good_matches = []
    for m,n in matches:
        if m.distance < 0.75*n.distance:
            # Get coordinate of the match
            m_x = int(q_k[m.queryIdx].pt[0])
            m_y = int(q_k[m.queryIdx].pt[1])
            good_matches.append(m)
            cv2.circle(crop_img, (int(q_k[m.queryIdx].pt[0]), int(q_k[m.queryIdx].pt[1])), 2, [0, 200, 200], 2)
    cv2.imshow('matches', crop_img)
    cv2.waitKey(0)

if __name__ == '__main__':
    match_object(previous =[126,268,786,652], 
                 current = './gstore-snippets/cookie_snippet/cookie_00274.jpg', 
                 train_img = './OT-res/KP-detect/cookie/cookie-train.jpg')