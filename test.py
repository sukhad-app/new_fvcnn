import sys
import pickle
sys.path.append('/root/opencv/build/lib')
import cv2
import tensorflow as tf
import sklearn 
import scipy
import glob
import numpy as np
import cPickle
from lxml import etree
from PIL import Image
from keras.applications.vgg16 import VGG16
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input
import pdb

from sklearn.datasets import make_classification
from sklearn.mixture import GMM


#img_path = '/home/sukhad/torch-feature-extract/images/1_4.jpg'
def fisher_vector(xx, gmm):
    xx = np.atleast_2d(xx)
    N = xx.shape[0]

    # Compute posterior probabilities.
    Q = gmm.predict_proba(xx)  # NxK

    # Compute the sufficient statistics of descriptors.
    Q_sum = np.sum(Q, 0)[:, np.newaxis] / N
    Q_xx = np.dot(Q.T, xx) / N
    Q_xx_2 = np.dot(Q.T, xx ** 2) / N

    # Compute derivatives with respect to mixing weights, means and variances.
    d_pi = Q_sum.squeeze() - gmm.weights_
    d_mu = Q_xx - Q_sum * gmm.means_
    d_sigma = (
        - Q_xx_2
        - Q_sum * gmm.means_ ** 2
        + Q_sum * gmm.covars_
        + 2 * Q_xx * gmm.means_)

    # Merge derivatives into a vector.
    return np.hstack((d_pi, d_mu.flatten(), d_sigma.flatten()))

if __name__=='__main__':
    model = VGG16(weights='imagenet', include_top=False)
    with open('model.pkl','rb') as fid:
        loaded = cPickle.load(fid)  
    print "loaded"
    video = cv2.VideoCapture('ab.mp4')
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640,480))
    while(True):
        frame,src = video.read()
        if(type(src)==type(None)):
            print "no video"
            continue
        dst = cv2.cvtColor(src,cv2.COLOR_BGR2GRAY)
        src1 = src.copy()
        blur = cv2.blur(dst,(7,7))
        edges = cv2.Canny(blur,20,100)
        kernel = np.ones((5,5), np.uint8)
        img_dilation = cv2.dilate(edges, kernel, iterations=2)
        _, contours, _= cv2.findContours(img_dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        X = []
        i = 0
        for cnt in contours:
            print "i"
            print i
            check =[]
            x,y,w,h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if(area>200 and area <100000):
                img1 = src[y:y+h,x:x+w]
                img1 = cv2.resize(img1,(50,50))
                x1 = image.img_to_array(img1)
                x1 = np.expand_dims(x1, axis=0)
                x1 = preprocess_input(x1)
                features = model.predict(x1)
                features = features.reshape(1,512)
                features = features.tolist()
                X.append(features[0])
                gmm = pickle.load(open('gmm_model.pkl', 'rb'))
                fv=fisher_vector(X[i],gmm)
                a = loaded.predict(fv)
                print a
                abc = src
                if(a==1):
                    abc = cv2.rectangle(abc,(x,y),(x+w,y+h),(0,255,0),2)
                i = i + 1
        out.write(abc)
        print "done"
