import cv2
import numpy as np 
import scipy as sp 


def match_object(previous, current, train_img, pos, frame, show = False):
    """

    Takes in:
        previous -> center of the previous image
        current ->  image being analyzed (with path)
        train_img -> training image for keypoint matching
        pos -> corners (left top, right bottom) of object in trianing img
        show -> determines if visualization is displayed
    Outputs:
        ??

    """
    #Take in training image with coordinates of tracked object
    t_img = cv2.imread(train_img)

    #query image
    q_img = cv2.imread(current)

    x1 = pos[2]
    y1 = pos[3]
    x2 = pos[0]
    y2 = pos[1]

    #I choose YOU! ORB-achu or SIFT-emon
    detector = cv2.SIFT()

    #crops image to reduce the neccessary search area
    t_k, t_d = detector.detectAndCompute(t_img, None)      #training image
    train_d = []
    train_k = []
    for index in range(len(t_k)):
        if x1<=t_k[index].pt[0]<= x2 and y1<= t_k[index].pt[1] <=y2:
            train_d.append(t_d[index])
            train_k.append(t_k[index])
    t_d = train_d
    t_k = train_k

    #Crop the query image with a 50% padding (calculate padding w/ height and width)
    h = y2 - y1 
    w = x2 - x1
    # big_img = q_img
    # q_img = q_img[(y1-0.5*h):(y2+0.5*h), (x1-0.5*w):(x2+0.5*w)]

    #create a list of keypoints for entire image, subtract out tracked object keypoints
    # t_k, t_d = detector.detectAndCompute(t_img, None)      #training image
    q_k, q_d = detector.detectAndCompute(q_img, None)      #query image

    # #finds all keypoints in the query image    
    # for kp in q_k:
    #     x_temp = kp.pt[0]
    #     y_temp = kp.pt[1]
    #     cv2.circle(q_img, (int(x_temp), int(y_temp)), 2, [255, 255, 0], 3)

    try:
        matcher = cv2.BFMatcher() #(normType = cv2.NORM_HAMMING)

        # for kp in t_k:
        #     x_temp = kp.pt[0]
        #     y_temp = kp.pt[1]
        #     cv2.circle(t_img, (int(x_temp), int(y_temp)), 2, [255, 255, 0], 3)

        # for kp in q_k:
        #     x_temp = kp.pt[0]
        #     y_temp = kp.pt[1]
        #     cv2.circle(q_img, (int(x_temp), int(y_temp)), 2, [255, 255, 0], 3)

        # #match list of object keypoints to list of remaining matches 
        matches = matcher.knnMatch(np.array(t_d), q_d, k =2)

        good_matches = []
        for m,n in matches:
            if m.distance < 0.75*n.distance:
                # Get coordinate of the match
                m_x = int(q_k[m.trainIdx].pt[0])
                m_y = int(q_k[m.trainIdx].pt[1])
                good_matches.append((m_x, m_y))

        for kp in good_matches:
            cv2.circle(q_img, kp, 2, [255, 0, 0], 3)

        # cv2.imshow('seeing all the kps', q_img)
        # cv2.waitKey(0)


        new_center, img_radius = mean_shift(hypothesis = (previous), 
                                            keypoints = good_matches, 
                                            threshold = 10, 
                                            current = q_img,
                                            show = True, 
                                            frame = frame)

        # new_center = (new_center[0]+(x1-0.5*w), new_center[1]+(y1-0.5*h))


        # if show:
        #     cv2.circle(big_img, (int(new_center[0]), int(new_center[1])), img_radius, [100,255,0], 2)
        #     cv2.imshow('big Match %d' % frame, big_img)
        #     cv2.waitKey(0)
        return new_center

    except Exception as inst:
        print inst
        # cv2.imshow('Frame %d : Likely there are no matches?' % frame, q_img)
        # cv2.waitKey(0)
        print "Likely there are no matches"
        return center

def mean_shift(hypothesis, keypoints, threshold, frame, current = None, show = False):
    """
    Inputs:
        hypothesis -> Previous center point as a starting hypothesis
        keypoints -> List of keypoint (x,y) coordinates
        Threshold -> maximum acceptable difference in center between iterations (eg 10 pixels, 5 pixels)
        current -> np array representing the image (for visualization)
        show -> determines whether visualization is shown

    Returns:
        New center of keypoints
        Radius
        If show is true -> displays the center, keypoints and a circle around the object
    """

    if len(keypoints) > 1:

        #assigns a value to the weighting constant -> based on 
        #experimental results on cropped cookie_00274
        c = 0.00001

        #arbitrarily set diff high to go through loop at least once
        diff = 1000

        while(diff > threshold):
            #sets up lists of weights and weights*position
            x_weights = []
            y_weights = []
            weighted_x = []
            weighted_y = []
            #Creats a list of weighted points, where points near the 
            #hypothesis have a larger weight
            last_guess = hypothesis
            for kp in keypoints:
                x_val = np.exp(-c * (kp[0] - last_guess[0])**2)
                x_weights.append(x_val)
                weighted_x.append(x_val*kp[0])
                y_val = np.exp(-c * (kp[1] - last_guess[1])**2)
                y_weights.append(y_val)
                weighted_y.append(y_val*kp[1])

            #finds 'center of mass' of the points to determine new center
            x = int(sum(weighted_x)/sum(x_weights))
            y = int(sum(weighted_y)/sum(y_weights))

            #update hypothesis
            hypothesis = (x,y)

            diff = np.sqrt((last_guess[0] - x)**2 + (last_guess[1] - y)**2)

            # Finding the radius:
            norm_weights = [np.linalg.norm([x_weights[i], y_weights[i]]) for i in range(len(x_weights))]
            avg_weight = sum(norm_weights)/len(norm_weights)
            std_weight = np.std(norm_weights)

            # Threshold based on standard deviations (to account for different kp density scenarios)
            threshold = avg_weight #- .25*std_weight
            inliers = []

            # Radius corresponds to the farthest-away keypoints are in the threshold from center of mass (x,y)
            for index in range(len(norm_weights)):
                if norm_weights[index] > threshold:
                    coords = [keypoints[index][0] - x, keypoints[index][1] - y] 
                    inliers.append(np.linalg.norm(coords))
            radius = int(max(inliers))

        #visualizes moving center and displays keypoints
        if show:
            img = current   #Needs to be np array (alread opened by cv2)
            for k in keypoints:
                cv2.circle(img, k, 2, [255, 0, 0], 2)
            cv2.circle(img, hypothesis, 3, [0, 0, 255], 3)
            cv2.circle(img, hypothesis, radius, [100,255,0], 2)
            cv2.imshow('Frame %d: Current hypothesis' % frame, img)
            # cv2.imwrite('./OT-res/meanshift/cookie/halfwidth_177.jpg', img)
            cv2.waitKey(0)
            # cv2.destroyWindow('Frame %d: Current hypothesis' % frame)
        return hypothesis, radius

    elif len(keypoints) == 1: # That moment when there's only one good match and the stdev of a single element set is zero...

        hypothesis = (keypoints[0][0], keypoints[0][1])
        radius = 10

        #visualizes moving center and displays keypoints
        if show:
            img = current   #Needs to be np array (alread opened by cv2)
            cv2.circle(img, hypothesis, 3, [0, 0, 255], 3)
            cv2.circle(img, hypothesis, radius, [100,255,0], 2)
            # cv2.imwrite('./OT-res/meanshift/cookie/cookie_00%d.jpg' % frame, img)
            cv2.imshow('Frame %d: Current hypothesis' % frame, img)
            cv2.waitKey(0)
            # cv2.destroyWindow('Frame %d: Current hypothesis' % frame)

        return hypothesis, radius

 
if __name__ == '__main__':
    # initial values for prototyping w/ the cookies. :P
    old_center = [600, 470]
    center = old_center
    pos = [744,514,606,392]

    for frame in range(177,280): 
        cv2.destroyAllWindows()
        print "Frame number: %d" % frame
        center = match_object(previous = center, 
                              current = './gstore-snippets/cookie_snippet/cookie_00%d.jpg' % frame, 
                              train_img = './gstore-snippets/cookie_snippet/cookie_00177.jpg',
                              pos = pos,
                              show = True,
                              frame = frame)
        print "center: (%d, %d)" % (center[0], center[1])
        print "old_center: (%d, %d)" % (old_center[0], old_center[1])
        delta_x = center[0]-old_center[0]
        delta_y = center[1]-old_center[1]


        print "delta_x: %d " % delta_x
        print "delta_y: %d " % delta_y

        max_center_delta = 5
        if delta_x >= max_center_delta: #prevent center from moving more than 5 pixels (some threshold number...) in an iteration 
            delta_x = max_center_delta
        elif delta_x <= -1 * max_center_delta:
            delta_x = -1 * max_center_delta

        if delta_y >= max_center_delta: #prevent center from moving more than 5 pixels (some threshold number...) in an iteration 
            delta_y = max_center_delta
        elif delta_y <= -1 * max_center_delta:
            delta_y = -1 * max_center_delta

        print "delta_x: %d " % delta_x
        print "delta_y: %d " % delta_y
    

        old_center = center
        pos = [pos[0]+delta_x +1, pos[1]+delta_y+1, pos[2]+delta_x -1, pos[3]+delta_y -1]