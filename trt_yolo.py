"""trt_yolo.py

This script demonstrates how to do real-time object detection with
TensorRT optimized YOLO engine.
"""


import os
import time
import argparse

import cv2
import pycuda.autoinit  # This is needed for initializing CUDA driver
import numpy as np

from multiprocessing import Process
import multiprocessing

from utils.yolo_classes import get_cls_dict
from utils.camera import add_camera_args, Camera
from utils.display import open_window, set_display, show_fps
from utils.visualization import BBoxVisualization

from utils.yolo_with_plugins import TrtYOLO

import pycuda.driver as cuda
import pycuda.autoinit

dic_class={0:'insulator'}

WINDOW_NAME = 'TrtYOLODemo'

# os.environ[“CUDA_VISIBLE_DEVICES”]=“0”
os.environ["CUDA_VISIBLE_DEVICES"]="0"
def parse_args():
    """Parse input arguments."""
    desc = ('Capture and display live camera video, while doing '
            'real-time object detection with TensorRT optimized '
            'YOLO model on Jetson')

    parser = argparse.ArgumentParser(description=desc)
    parser = add_camera_args(parser)

    parser.add_argument(
        '-c', '--category_num', type=int, default=1,
        help='number of object categories [80]')
    parser.add_argument(
        '-m', '--model', type=str, default='yolov3-416')
    args = parser.parse_args()
    return args


def loop_and_detect(cam, trt_yolo, conf_th, vis):
    """Continuously capture images from camera and do object detection.

    # Arguments
      cam: the camera instance (video source).
      trt_yolo: the TRT YOLO object detector instance.
      conf_th: confidence/score threshold for object detection.
      vis: for visualization.
    """
    full_scrn = False
    fps = 0.0
    tic = time.time()
    while True:
        # if cv2.getWindowProperty(WINDOW_NAME, 0) < 0:
        #     break
        img = cam.read()
        if img is None:
            break
        boxes, confs, clss = trt_yolo.detect(img, conf_th)
        # result=np.stack((clss,confs),axis=1)
        # result=np.column_stack((result,boxes))
        # print("The number of insulator we detected :%d"%len(result))
        # print("The confidence of detection result: ",confs)
        # print("The class of detection result: ",dic_class[clss[0]])
        # print("The bounding box of detection result:\n",boxes)
        #
        # print(result)


        img = vis.draw_bboxes(img, boxes, confs, clss)
        img = show_fps(img, fps)

        cv2.imwrite("./result.jpg",img)
        # cv2.imshow(WINDOW_NAME, img)
        toc = time.time()
        curr_fps = 1.0 / (toc - tic)
        # calculate an exponentially decaying average of fps number
        fps = curr_fps if fps == 0.0 else (fps*0.95 + curr_fps*0.05)
        tic = toc
        key = cv2.waitKey(1)
        if fps>0:  # ESC key: quit program
            break



def yolo_detection():
    # dev = cuda.Device(0)
    # ctx = dev.make_context()
    args = parse_args()
    print(args)
    """
    config  assert
    """
    if args.category_num <= 0:
        raise SystemExit('ERROR: bad category_num (%d)!' % args.category_num)
    if not os.path.isfile('yolo/darknet/%s.trt' % args.model):
        raise SystemExit('ERROR: file (yolo/darknet/%s.trt) not found!' % args.model)
    cls_dict = get_cls_dict(args.category_num)
    yolo_dim = args.model.split('-')[-1]

    if 'x' in yolo_dim:
        dim_split = yolo_dim.split('x')
        if len(dim_split) != 2:
            raise SystemExit('ERROR: bad yolo_dim (%s)!' % yolo_dim)
        w, h = int(dim_split[0]), int(dim_split[1])
    else:
        h = w = int(yolo_dim)
    if h % 32 != 0 or w % 32 != 0:
        raise SystemExit('ERROR: bad yolo_dim (%s)!' % yolo_dim)

    """
    capture the image
    """
    cam = Camera(args)
    if not cam.isOpened():
        raise SystemExit('ERROR: failed to open camera!')

    """
    deploy the yolo model
    """
    trt_yolo = TrtYOLO(args.model, (h, w), args.category_num)

    # open_window(
    #     WINDOW_NAME, 'Camera TensorRT YOLO Demo',
    #     cam.img_width, cam.img_height)
    """
    detect the insulator using model
    """
    vis = BBoxVisualization(cls_dict)
    loop_and_detect(cam, trt_yolo, conf_th=0.3, vis=vis)

    """
    release the image
    """

    cam.release()
    # cv2.destroyAllWindows()
    # print("Hi!")
    # ctx.pop()
    # del ctx




class TestProcess(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)
        # self.ctx

    def run(self):

        print('⼦进程运⾏中')
        yolo_detection()
        print('⼦进程结束')


if __name__ == '__main__':

    # yolo_detection()

    # print(ctx)
    multiprocessing.set_start_method('spawn')
    t=TestProcess()

    t.daemo=True
    t.start()

