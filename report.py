import os
import matplotlib.pyplot as plt
from predict import predict
from tqdm import tqdm
import argparse
import csv
from dataset_scripts.metrics_eval import evaluate_detections, extract_mAP, extract_AP, get_classes
import json
import sys
from dataset_scripts.utils.coco_tools import leave_boxes


def build_parser():
    if ('-name' in sys.argv) or ('--name' in sys.argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('-name', '--name', required=True, type=str)
        parser.add_argument('-cfg', '--yolo-cfg-name', type=str, default='yolov3.cfg')
        parser.add_argument('-dataset', '--dataset-name', type=str)
        parser.add_argument('-drk-lfd', '--darknet-folder', type=str, default='')
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument('-cfg', '--config-file', required=True, type=str)
        parser.add_argument('-models-fld', '--models-folder', required=True, type=str)
        parser.add_argument('-rep-fld', '--report-folder', required=True, type=str)
        parser.add_argument('-img-fld', '--images-folder', required=True, type=str)
        parser.add_argument('-ann', '--annotations-file', required=True, type=str)
    parser.add_argument('-area', '--area', nargs=2, type=str, default=['0**2', '1e5**2'])
    parser.add_argument('-shape', '--shape', nargs=2, type=int, default=(None, None))
    parser.add_argument('-add', '--add', action='store_true')
    parser.add_argument('-dont-repredict', '--dont-repredict', dest='repredict', action='store_false')
    parser.add_argument('-gpu', '--gpu', type=int, default=0)
    return parser


def get_existing_information(report_folder):
    existing_epochs, existing_metrics = list(), list()
    with open(os.path.join(report_folder, 'metrics.csv'), 'r') as f:
        existing_information = csv.reader(f, delimiter=' ')
        for new_information in existing_information:
            existing_epochs.append(int(new_information[0]))
            existing_metrics.append(list(map(float, new_information[1:])))
    return existing_epochs, existing_metrics


def create_folders(report_folder):
    if not os.path.exists(report_folder):
        os.mkdir(report_folder)
    if not os.path.exists(os.path.join(report_folder, 'predictions')):
        os.mkdir(os.path.join(report_folder, 'predictions'))


def get_models_files(models_folder, existing_epochs):
    models_files = os.listdir(models_folder)
    epochs = []
    for i in range(len(models_files)-1, -1, -1):
        if models_files[i].startswith("epoch"):
            epoch = int(models_files[i][6:-8])
            if epoch not in existing_epochs:
                epochs.insert(0, epoch)
                models_files[i] = os.path.join(models_folder, models_files[i])
            else:
                del models_files[i]
        else:
            del models_files[i]
    return models_files, epochs


def run_models(config_file, models_files, epochs, report_folder, images_folder, annotations_file, repredict=True):
    for model_file, epoch in tqdm(list(zip(models_files, epochs))):
        out_file = os.path.join(report_folder, 'predictions', 'epoch_{}.json'.format(epoch))
        if os.path.exists(out_file) and not repredict:
            continue
        predict(config_file, model_file, images_folder, out_file=out_file, predict_to='coco', detections_only=True,
                images_file=annotations_file, classes_file=annotations_file, threshold=0.01, max_dets=100)


def calculate_metrics(epochs, report_folder, annotations_file, area, shape=(None, None)):
    metrics = list()
    # kostil' #
    indexes_to_correct = list()
    ###########
    with open(annotations_file, 'r') as f:
        annotations_dict = json.load(f)
    leave_boxes(annotations_dict, area, width=shape[0], height=shape[1])

    for epoch in tqdm(epochs):
        detections_file = os.path.join(report_folder, 'predictions/epoch_{}.json'.format(epoch))
        with open(detections_file, 'r') as f:
            detections_dict = json.load(f)
        # kostil' #
        if detections_dict == list():
            metrics.append(None)
            indexes_to_correct.append(len(metrics)-1)
            continue
        ###########
        detections_dict_with_images = {'images': annotations_dict['images'], 'annotations': detections_dict}
        leave_boxes(detections_dict_with_images, area, width=shape[0], height=shape[1])
        detections_dict = detections_dict_with_images['annotations']
        results = evaluate_detections(annotations_dict, detections_dict)
        classes = get_classes(results)
        metric = [extract_mAP(results)]
        metric += extract_AP(results, classes)
        metrics.append(metric)
    # kostil' #
    for index in indexes_to_correct:
        metrics[index] = [0] * (len(classes)+1)
    ###########
    return metrics, classes


def save_metrics(epochs, metrics, classes, report_folder):
    with open(os.path.join(report_folder, 'metrics.csv'), 'w') as f:
        writer = csv.writer(f, delimiter=' ')
        for epoch, metric in zip(epochs, metrics):
            writer.writerow([epoch] + metric)
    with open(os.path.join(report_folder, 'classes.txt'), 'w') as f:
        for i, cl in enumerate(classes):
            f.write(cl)
            if i != len(classes)-1:
                f.write(' ')
    mAP = list()
    APs = list()
    for metric in metrics:
        mAP.append(metric[0])
        APs.append(metric[1:])
    plt.plot(epochs, mAP)
    plt.grid()
    plt.savefig(os.path.join(report_folder, 'mAP.png'))
    plt.close()
    plt.plot(epochs, APs)
    plt.grid()
    plt.savefig(os.path.join(report_folder, 'APs.png'))
    plt.close()


def report(config_file, models_folder, report_folder, images_folder, annotations_file,
           area=(0**2, 1e5**2), shape=(None, None), add=False, repredict=True):
    if area[1] == -1:
        area = (area[0], 1e5**2)
    if add:
        existing_epochs, existing_metrics = get_existing_information(report_folder)
    else:
        existing_epochs, existing_metrics = list(), list()
    create_folders(report_folder)
    models_files, epochs = get_models_files(models_folder, existing_epochs)
    run_models(config_file, models_files, epochs, report_folder, images_folder, annotations_file, repredict=repredict)
    metrics, classes = calculate_metrics(epochs, report_folder, annotations_file, area, shape=shape)
    epochs += existing_epochs
    metrics += existing_metrics
    epochs, metrics = zip(*sorted(zip(epochs, metrics)))
    save_metrics(epochs, metrics, classes, report_folder)


def complete_args(kwargs):
    name = kwargs.pop('name')
    darknet_folder = kwargs.pop('darknet_folder')
    yolo_cfg_name = kwargs.pop('yolo_cfg_name')
    dataset_name = kwargs.pop('dataset_name')
    if dataset_name is None:
        dataset_name = name
    kwargs['config_file'] = os.path.join(darknet_folder, name, 'config/'+yolo_cfg_name)
    kwargs['models_folder'] = os.path.join(darknet_folder, name)
    kwargs['report_folder'] = os.path.join(darknet_folder, name, 'report/')
    kwargs['images_folder'] = os.path.join(darknet_folder, 'data', dataset_name, 'images/test/')
    kwargs['annotations_file'] = os.path.join(darknet_folder, 'data', dataset_name, 'test.json')


if __name__ == '__main__':
    parser = build_parser()
    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    args.area = list(map(eval, args.area))
    kwargs = vars(args)
    kwargs.pop('gpu')
    if 'name' in kwargs.keys():
        complete_args(kwargs)
    report(**kwargs)
