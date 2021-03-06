import argparse
import os
from darknet import load_network, detect_image_letterbox, free_network_ptr, resize_network, get_class_id_to_name, load_image, free_image
import json
import xml.etree.ElementTree as xml
from xml.dom import minidom
from PIL import Image
from tqdm import tqdm


class Predictions:
    def __init__(self):
        self.bboxes = list()
        self.scores = list()
        self.classes = list()


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfg', '--config-file', required=True, type=str)
    parser.add_argument('-net', '--network-file', required=True, type=str)
    parser.add_argument('-img-fld', '--images-folder', required=True, type=str)
    parser.add_argument('-out', '--out-file', required=True, type=str)
    parser.add_argument('-to', '--predict-to', type=str, choices=['cvat', 'coco'], default='coco')
    parser.add_argument('-dets-only', '--detections-only', action='store_true')
    parser.add_argument('-img', '--images-file', type=str)
    parser.add_argument('-cls', '--classes-file', type=str)
    parser.add_argument('-thr', '--threshold', type=float, default=0.001)
    parser.add_argument('-max-dets', '--max-dets', type=int, default=1000, help='Maximum detections per image')
    parser.add_argument('-nms', '--nms', type=float, default=0.45)
    parser.add_argument('-is', '--input-shape', type=int, nargs=2, default=[None, None])
    parser.add_argument('-gpu', '--gpu', type=int, default=0)
    return parser


def get_images(images_folder, images_file=None):
    if images_file is None:
        return get_images_from_folder(images_folder)
    if images_file.endswith('.json'):
        return get_images_from_json(images_folder, images_file)
    if images_file.endswith('.txt'):
        return get_images_from_list(images_folder, images_file)
    return None, None, None


def get_images_from_folder(images_folder):
    images_names = sorted(os.listdir(images_folder))
    images_ids, images_files = list(), list()
    image_id = 0
    for image_name in images_names:
        images_ids.append(image_id)
        image_id += 1
        images_files.append(os.path.join(images_folder, image_name))
    return images_names, images_ids, images_files


def get_images_from_json(images_folder, json_file):
    with open(json_file, 'r') as f:
        json_dict = json.load(f)
    images = json_dict['images']
    images_names, images_ids, images_files = list(), list(), list()
    for image in images:
        images_names.append(image['file_name'])
        images_ids.append(image['id'])
        images_files.append(os.path.join(images_folder, image['file_name']))
    return images_names, images_ids, images_files


def get_images_from_list(images_folder, list_file):
    with open(list_file, 'r') as f:
        images_names = f.readlines()
    images_ids, images_files = list(), list()
    for i, image_name in enumerate(images_names):
        if image_name[-1] == '\n':
            image_name = image_name[:-1]
            images_names[i] = image_name
        images_ids.append(i)
        images_files.append(os.path.join(images_folder, image_name))
    return images_names, images_ids, images_files


def init_out_data(images_num, class_id_to_name, predict_to='coco'):
    if predict_to == 'cvat':
        return init_cvat(images_num, class_id_to_name)
    if predict_to == 'coco':
        return init_coco(class_id_to_name)
    return None


def init_cvat(images_num, class_id_to_name):
    annotations = xml.Element("annotations")
    meta = xml.SubElement(annotations, "meta")
    task = xml.SubElement(meta, "task")
    size = xml.SubElement(task, "size").text = str(images_num)
    mode = xml.SubElement(task, "mode").text = "annotation"
    overlap = xml.SubElement(task, "overlap").text = "0"
    flipped = xml.SubElement(task, "flipped").text = "False"
    labels = xml.SubElement(task, "labels")
    classes = list(zip(*sorted(class_id_to_name.items())))[1]
    num_classes = len(classes)
    for cl in classes:
        label = xml.SubElement(labels, "label")
        name = xml.SubElement(label, "name").text = cl
    return annotations


def init_coco(class_id_to_name):
    json_dict = {'images': list(), 'annotations': list(), 'categories': list()}
    for class_id, class_name in class_id_to_name.items():
        category = {'name': class_name, 'id': class_id+1}
        json_dict['categories'].append(category)
    return json_dict


def add_predictions_to_out_data(image_name, image_id, width, height, predictions, out_data, class_id_to_name, predict_to='coco'):
    if predict_to == 'cvat':
        return add_predictions_to_cvat(image_name, image_id, width, height, predictions, class_id_to_name, out_data)
    if predict_to == 'coco':
        return add_predictions_to_coco(image_name, image_id, width, height, predictions, out_data)


def add_predictions_to_cvat(image_name, image_id, width, height, predictions, class_id_to_name, out_data):
    image = dict()
    image['id'] = str(image_id)
    image['name'] = image_name
    image['width'] = str(width)
    image['height'] = str(height)
    xml_image = xml.SubElement(out_data, "image", image)

    for cl, score, bbox in predictions:
        image_bbox = dict()
        image_bbox['label'] = class_id_to_name[cl]
        image_bbox['occluded'] = '0'
        left = max(bbox[0] - bbox[2] / 2, 0)
        top = max(bbox[1] - bbox[3] / 2, 0)
        right = min(bbox[0] + bbox[2] / 2, width)
        bottom = min(bbox[1] + bbox[3] / 2, height)
        image_bbox['xtl'] = left
        image_bbox['ytl'] = top
        image_bbox['xbr'] = right
        image_bbox['ybr'] = bottom
        image_bbox['score'] = str(score)
        xml.SubElement(xml_image, "box", image_bbox)


def add_predictions_to_coco(image_name, image_id, width, height, predictions, out_data):
    image = dict()
    image['id'] = image_id
    image['file_name'] = image_name
    image['width'] = width
    image['height'] = height
    out_data['images'].append(image)

    for cl, score, bbox in predictions:
        annotation = dict()
        if len(out_data['annotations']) == 0:
            annotation['id'] = 1
        else:
            annotation['id'] = out_data['annotations'][-1]['id'] + 1
        annotation['iscrowd'] = 0
        annotation['image_id'] = image_id
        annotation['category_id'] = cl + 1
        left = max(bbox[0] - bbox[2] / 2, 0)
        top = max(bbox[1] - bbox[3] / 2, 0)
        right = min(bbox[0] + bbox[2] / 2, width)
        bottom = min(bbox[1] + bbox[3] / 2, height)
        annotation['bbox'] = [left, top, right - left, bottom - top]
        annotation['area'] = annotation['bbox'][2] * annotation['bbox'][3]
        annotation['score'] = score
        out_data['annotations'].append(annotation)


def do_predictions(network, images_names, images_ids, images_files, class_id_to_name, threshold=0.001, max_dets=1000,
                   nms=0.45, predict_to='cvat'):
    out_data = init_out_data(len(images_files), class_id_to_name, predict_to=predict_to)
    for image_name, image_id, image_file in tqdm(list(zip(images_names, images_ids, images_files))):
        image = load_image(image_file.encode(), 0, 0)
        predictions = detect_image_letterbox(network, image_file, max_dets=max_dets, thresh=threshold, nms=nms)
        width, height = int(image.w), int(image.h)
        free_image(image)
        add_predictions_to_out_data(image_name, image_id, width, height, predictions, out_data, class_id_to_name,
                                    predict_to=predict_to)
    return out_data


def save_predictions(out_file, out_data, predict_to='coco'):
    if predict_to == 'cvat':
        save_predictions_to_cvat(out_file, out_data)
    if predict_to == 'coco':
        save_predictions_to_coco(out_file, out_data)


def save_predictions_to_cvat(out_file, out_data):
    rough_string = xml.tostring(out_data, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    with open(out_file, "w") as f:
        f.writelines(reparsed.toprettyxml(indent='  '))


def save_predictions_to_coco(out_file, out_data):
    with open(out_file, 'w') as f:
        json.dump(out_data, f, indent=2)


def predict(config_file, network_file, images_folder, out_file=None, predict_to='coco', detections_only=False,
            images_file=None, classes_file=None, threshold=0.001, max_dets=1000, nms=0.45, input_shape=(None, None)):
    if predict_to not in ('coco', 'cvat'):
        raise RuntimeError()
    if len(input_shape) != 2:
        raise RuntimeError()
    network = load_network(config_file, None, network_file)
    if input_shape[0] is not None:
        input_shape = tuple(map(lambda x: max(round(x/32) * 32, 32), input_shape))
        resize_network(network, input_shape[0], input_shape[1])
    images_names, images_ids, images_files = get_images(images_folder, images_file=images_file)
    class_id_to_name = get_class_id_to_name(classes_file=classes_file)
    out_data = do_predictions(network, images_names, images_ids, images_files, class_id_to_name, threshold=threshold,
                              max_dets=max_dets, nms=nms, predict_to=predict_to)
    free_network_ptr(network)
    if (predict_to == 'coco') and detections_only:
        out_data = out_data['annotations']
    if out_file:
        save_predictions(out_file, out_data, predict_to=predict_to)
    return out_data


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    kwargs = vars(args)
    kwargs.pop('gpu')
    predict(**kwargs)
