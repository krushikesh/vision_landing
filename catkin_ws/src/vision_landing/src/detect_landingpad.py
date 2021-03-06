#!/usr/bin/env python
import roslib
import sys
import rospy
import cv2
import numpy as np
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Vector3

class image_converter:

  def __init__(self):
    self.image_pub = rospy.Publisher("image_with_blob",Image, queue_size=1)
    self.pixel_pub = rospy.Publisher("pixel_coordinates",Vector3,  queue_size=1)

    self.bridge = CvBridge()
    self.image_sub = rospy.Subscriber("/usb_cam/image_raw",Image,self.callback)

    #create blob detector parameter object
    self.params = cv2.SimpleBlobDetector_Params()
    #filter by size
    self.params.filterByArea = True
    self.params.minArea = 100
    #filter by circularity
    self.params.filterByCircularity = True
    self.params.minCircularity = 0.5
    #filter by convexity
    self.params.filterByConvexity = True
    self.params.minConvexity = 0.87
    #filter by inertia
    self.params.filterByInertia = True
    self.params.minInertiaRatio = 0.35
    #create blob detector with params object
    self.blob_detect = cv2.SimpleBlobDetector_create(self.params)   #openCV3
    #self.blob_detect = cv2.SimpleBlobDetector(self.params)  #openCV2

    #create videowriter object
    fps = 15
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    self.out = cv2.VideoWriter()
    success = self.out.open('/home/hummingbird1/Desktop/test_vid2.avi',fourcc,fps,(640,480),True)

  def callback(self,data):
    try:
      cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
    except CvBridgeError as e:
      print(e)

    #__Process the image to find the target pixel location

    #__BEGIN PLAIN THRESHOLD METHOD__
    #convert to grayscale
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    #threshold
    _, gray_thresh = cv2.threshold(gray, 230, 255, 1)
    #erode to kill the noise
    #kernel = np.zeros((11,11),np.uint8)
    #gray_erode = cv2.erode(gray_thresh,kernel,iterations = 1)
    #__END PLAIN THRESHOLD METHOD__

    #detect blobs and get keypoints
    keypoints = self.blob_detect.detect(gray_thresh)

    #create a Vector3 object
    pixel = Vector3()

    #Check to make sure there's only one blob found
    if len(keypoints) == 1:
        for p in keypoints:
            x_coord = p.pt[0]
            y_coord = p.pt[1]

            #shift coordinates to be relative to center
            x_coord = x_coord - 320
            y_coord = y_coord - 240
            pixel.x = x_coord
            pixel.y = y_coord
            pixel.z = 1
    else:
        pixel.x = 0
        pixel.y = 0
        pixel.z = 0

    #publish the pixel location of the target
    self.pixel_pub.publish(pixel)

    #draw keypoints
    img_w_keypoints = cv2.drawKeypoints(cv_image,keypoints,np.array([]),(0,0,255),cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    #write the image to videowriter
    self.out.write(img_w_keypoints)

    #display the image
    #cv2.imshow("Image window", img_w_keypoints)
    #cv2.waitKey(3)

    #publish the image
    try:
      self.image_pub.publish(self.bridge.cv2_to_imgmsg(img_w_keypoints, "bgr8"))
    except CvBridgeError as e:
      print(e)



def main(args):
    rospy.init_node('image_converter', anonymous=True)
    ic = image_converter()
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down")
    cv2.destroyAllWindows()
    self.out.release()

if __name__ == '__main__':
    main(sys.argv)
