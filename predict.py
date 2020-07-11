import argparse
import os
from tools import init_model, detect, free_model, resize_model
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
    parser.add_argument('-model', '--model-file', required=True, type=str)
    parser.add_argument('-img-fld', '--images-folder', required=True, type=str)
    parser.add_argument('-out', '--out-file', required=True, type=str)
    parser.add_argument('-to', '--predict-to', type=str, choices=['cvat', 'coco'], default='coco')
    parser.add_argument('-dets-only', '--detections-only', action='store_true')
    parser.add_argument('-img', '--images-file', type=str)
    parser.add_argument('-cls', '--classes-file', type=str)
    parser.add_argument('-thr', '--threshold', type=float, default=0.001)
    parser.add_argument('-max-dets', '--max-dets', type=int, default=1000, help='Maximum detections per image')
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


def get_class_id_to_name(classes_file=None):
    if classes_file is None:
        return None
    if classes_file.endswith('.json'):
        return get_class_id_to_name_from_json(classes_file)
    if classes_file.endswith('.names'):
        return get_class_id_to_name_from_list(classes_file)
    return None


def get_class_id_to_name_from_json(json_file):
    with open(json_file, 'r') as f:
        json_dict = json.load(f)
    categories = json_dict['categories']
    class_id_to_name = dict()
    for category in categories:
        class_id_to_name[category['id']-1] = category['name']
    return class_id_to_name


def get_class_id_to_name_from_list(list_file):
    class_id_to_name = dict()
    class_id = 0
    with open(list_file, 'r') as f:
        classes_names = f.readlines()
    for class_name in classes_names:
        if class_name[-1] == '\n':
            class_name = class_name[:-1]
        class_id_to_name[class_id] = class_name
        class_id += 1
    return class_id_to_name


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


def add_predictions_to_out_data(image_name, image_id, image_file, bboxes, scores, classes, out_data, class_id_to_name, predict_to='coco'):
    if predict_to == 'cvat':
        return add_predictions_to_cvat(image_name, image_id, image_file, bboxes, scores, classes, class_id_to_name, out_data)
    if predict_to == 'coco':
        return add_predictions_to_coco(image_name, image_id, image_file, bboxes, scores, classes, out_data)


def add_predictions_to_cvat(image_name, image_id, image_file, bboxes, scores, classes, class_id_to_name, out_data):
    image = dict()
    image['id'] = str(image_id)
    image['name'] = image_name
    w, h = Image.open(image_file).size
    image['width'] = str(w)
    image['height'] = str(h)
    xml_image = xml.SubElement(out_data, "image", image)

    for bbox, score, cl in zip(bboxes, scores, classes):
        image_bbox = dict()
        image_bbox['label'] = class_id_to_name[cl]
        image_bbox['occluded'] = '0'
        image_bbox['xtl'] = str(max(bbox[0], 0))
        image_bbox['ytl'] = str(max(bbox[1], 0))
        image_bbox['xbr'] = str(min(bbox[2], w))
        image_bbox['ybr'] = str(min(bbox[3], h))
        image_bbox['score'] = str(score)
        xml.SubElement(xml_image, "box", image_bbox)


def add_predictions_to_coco(image_name, image_id, image_file, bboxes, scores, classes, out_data):
    image = dict()
    image['id'] = image_id
    image['file_name'] = image_name
    w, h = Image.open(image_file).size
    image['width'] = w
    image['height'] = h
    out_data['images'].append(image)

    for bbox, score, cl in zip(bboxes, scores, classes):
        annotation = dict()
        if len(out_data['annotations']) == 0:
            annotation['id'] = 1
        else:
            annotation['id'] = out_data['annotations'][-1]['id'] + 1
        annotation['iscrowd'] = 0
        annotation['image_id'] = image_id
        annotation['category_id'] = cl + 1
        annotation['bbox'] = [max(bbox[0], 0), max(bbox[1], 0),
                              min(bbox[2], w) - max(bbox[0], 0),
                              min(bbox[3], h) - max(bbox[1], 0)]
        annotation['area'] = annotation['bbox'][2] * annotation['bbox'][3]
        annotation['score'] = score
        out_data['annotations'].append(annotation)


def do_predictions(model, images_names, images_ids, images_files, class_id_to_name, threshold=0.001, max_dets=1000,
                   predict_to='cvat'):
    out_data = init_out_data(len(images_files), class_id_to_name, predict_to=predict_to)
    for image_name, image_id, image_file in tqdm(list(zip(images_names, images_ids, images_files))):
        bboxes, scores, classes = detect(model, image_file, max_dets=max_dets, threshold=threshold)
        add_predictions_to_out_data(image_name, image_id, image_file, bboxes, scores, classes, out_data, class_id_to_name,
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


def my_round(a):
    i = int(a)
    if a - i < 0.5:
        return i
    else:
        return i + 1


def predict(config_file, model_file, images_folder, out_file=None, predict_to='coco', detections_only=False,
            images_file=None, classes_file=None, threshold=0.001, max_dets=1000, input_shape=(None, None)):
    if predict_to not in ('coco', 'cvat'):
        raise RuntimeError()
    if len(input_shape) != 2:
        raise RuntimeError()
    model = init_model(config_file, model_file)
    if input_shape[0] is not None:
        input_shape = tuple(map(lambda x: max(my_round(x/32) * 32, 32), input_shape))
        resize_model(model, input_shape[0], input_shape[1])
    images_names, images_ids, images_files = get_images(images_folder, images_file=images_file)
    class_id_to_name = get_class_id_to_name(classes_file=classes_file)
    out_data = do_predictions(model, images_names, images_ids, images_files, class_id_to_name, threshold=threshold,
                              max_dets=max_dets, predict_to=predict_to)
    free_model(model)
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
