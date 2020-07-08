import ctypes
import argparse
import os
import numpy as np
import colorsys
from PIL import Image, ImageFont, ImageDraw
from time import time


class Box(ctypes.Structure):
    _fields_ = [('x', ctypes.c_float),
                ('y', ctypes.c_float),
                ('w', ctypes.c_float),
                ('h', ctypes.c_float)]


class Detection(ctypes.Structure):
    _fields_ = [('bbox', Box),
                ('classes', ctypes.c_int),
                ('prob', ctypes.POINTER(ctypes.c_float)),
                ('mask', ctypes.POINTER(ctypes.c_float)),
                ('objectness', ctypes.c_float),
                ('sort_class', ctypes.c_int),
                ('uc', ctypes.POINTER(ctypes.c_float)),
                ('points', ctypes.c_int)]


class Detections(ctypes.Structure):
    _fields_ = [('num', ctypes.c_int),
                ('dets', ctypes.POINTER(Detection))]


class IntPair(ctypes.Structure):
    _fields_ = [('x', ctypes.c_int),
                ('y', ctypes.c_int)]


lib = ctypes.cdll.LoadLibrary(os.path.join('./', os.path.dirname(__file__), 'libdarknet.so'))

lib.init_model.restype = ctypes.c_void_p
lib.init_model.argtypes = [ctypes.c_char_p, ctypes.c_char_p]

lib.free_model.argtypes = [ctypes.c_void_p, ]

lib.detect.restype = Detections
lib.detect.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_float, ctypes.c_float]

lib.free_detections.argtypes = [ctypes.POINTER(Detection), ctypes.c_int]

lib.get_model_input_shape.restype = IntPair
lib.get_model_input_shape.argtypes = [ctypes.c_void_p, ]

lib.resize_network.restype = ctypes.c_int
lib.resize_network.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfg', '--config-file', required=True, type=str)
    parser.add_argument('-model', '--model-file', required=True, type=str)
    parser.add_argument('-img', '--image-file', required=True, type=str)
    parser.add_argument('-gpu', '--gpu', type=int, default=0)
    return parser


def init_model(config_file, model_file):
    model = lib.init_model(config_file.encode(), model_file.encode())
    return model


def free_model(model):
    lib.free_model(model)


def free_detections(detections):
    lib.free_detections(detections.dets, detections.num)


def get_model_input_shape(model):
    shape = lib.get_model_input_shape(model)
    return shape.x, shape.y


def resize_model(model, w, h):
    return lib.resize_network(model, w, h)


#spent_time = 0
#counter = 0
def detect(model, image_file, max_dets=1000, threshold=0.001, nms=0.45):
    image = Image.open(image_file)
    width, height = image.width, image.height
    detections = lib.detect(model, image_file.encode(), threshold, nms)
    #global spent_time
    #global counter
    #time_now = time()
    if detections.num == 0:
        return list(), list(), list()
    bboxes = list()
    scores = list()
    classes = list()
    num_classes = detections.dets[0].classes
    for i in range(detections.num):
        for cl in range(num_classes):
            if detections.dets[i].prob[cl] < threshold:
                continue
            if detections.dets[i].points != 0:
                raise RuntimeError('Only center box cordinates supported\n')
            x = detections.dets[i].bbox.x
            y = detections.dets[i].bbox.y
            w = detections.dets[i].bbox.w
            h = detections.dets[i].bbox.h
            bbox = [(x - w / 2) * width, (y - h / 2) * height, (x + w / 2) * width, (y + h / 2) * height]
            bboxes.append(bbox)
            scores.append(detections.dets[i].prob[cl])
            classes.append(cl)
    free_detections(detections)
    if len(scores) > max_dets:
        scores, classes, bboxes = zip(*sorted(zip(scores, classes, bboxes), reverse=True)[:max_dets])
    #spent_time += (time() - time_now)
    #counter += 1
    #print(spent_time / counter * 1000)
    return bboxes, scores, classes


def draw_detections(original_image, bboxes, scores, classes, class_names, thr=0.1):
    image = original_image.copy()

    hsv_tuples = [(x / len(class_names), 1., 1.)
                  for x in range(len(class_names))]
    colors = list(map(lambda x: colorsys.hsv_to_rgb(*x), hsv_tuples))
    colors = list(
        map(lambda x: (int(x[0] * 255), int(x[1] * 255), int(x[2] * 255)),
            colors))

    font = ImageFont.truetype(font='font/FiraMono-Medium.otf',
                              size=np.floor(3e-2 * image.size[1] + 0.5).astype('int32'))
    thickness = (image.size[0] + image.size[1]) // 300

    for i, c in reversed(list(enumerate(classes))):
        if scores[i] < thr:
            continue

        predicted_class = class_names[c]
        box = bboxes[i]
        score = scores[i]

        label = '{} {:.2f}'.format(predicted_class, score)
        draw = ImageDraw.Draw(image)
        label_size = draw.textsize(label, font)

        left, top, right, bottom = box
        top = max(0, np.floor(top + 0.5).astype('int32'))
        left = max(0, np.floor(left + 0.5).astype('int32'))
        bottom = min(image.size[1], np.floor(bottom + 0.5).astype('int32'))
        right = min(image.size[0], np.floor(right + 0.5).astype('int32'))
        print(label, (left, top), (right, bottom))

        if top - label_size[1] >= 0:
            text_origin = np.array([left, top - label_size[1]])
        else:
            text_origin = np.array([left, top + 1])

        # My kingdom for a good redistributable image drawing library.
        for i in range(thickness):
            draw.rectangle(
                [left - i, top - i, right + i, bottom + i],
                outline=colors[c])
        draw.rectangle(
            [tuple(text_origin), tuple(text_origin + label_size)],
            fill=colors[c])
        draw.text(text_origin, label, fill=(0, 0, 0), font=font)
        del draw
    return image


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = str(args.gpu)
    kwargs = vars(args)
    kwargs.pop('gpu')
    model = init_model(args.config_file, args.model_file)
    bboxes, scores, classes = detect(model, args.image_file)
    free_model(model)
    class_names = [str(i) for i in range(80)]
    det_image = draw_detections(Image.open(args.image_file), bboxes, scores, classes, class_names, thr=0.3)
    #det_image.show()
    det_image.save('img.jpg')

