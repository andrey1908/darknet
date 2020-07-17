#include "darknet.h"
#include "parser.h"
#include <time.h>
#include <unistd.h>

typedef struct detections {
    int num;
    detection *dets;
} detections;

typedef struct int_pair {
    int x;
    int y;
} int_pair;

double what_time_is_it() {
    struct timespec now;
    clock_gettime(CLOCK_REALTIME, &now);
    return now.tv_sec + now.tv_nsec*1e-9;
}

network* init_model(char *cfg_file, char *weight_file) {
    network *model = (network*)malloc(sizeof(network));
    *model = parse_network_cfg_custom(cfg_file, 1, 1);
    load_weights(model, weight_file);
    model->benchmark_layers = 0;
    fuse_conv_batchnorm(*model);
    calculate_binary_weights(*model);
    return model;
}

void free_model(network* model) {
    free_network(*model);
    free(model);
}

int get_model_c(network* model) {
    return model->c;
}

detections detect(network* net, image im, float obj_thresh, float nms) {
    image sized = letterbox_image(im, net->w, net->h);
    //static double spent_time = 0;
    //static int counter = 0;
    //double start, end;
    //start = what_time_is_it();
    float *X = sized.data;
    network_predict(*net, X);
    int nboxes = 0;
    float hier_thresh = 0.5; //is not used in function 'get_network_boxes' for yolov3(4) model
    detection *dets = get_network_boxes(net, im.w, im.h, obj_thresh, hier_thresh, 0, 1, &nboxes, 1);
    if (nms > 0.) {
        layer l = net->layers[net->n - 1];
        if (l.nms_kind == DEFAULT_NMS) do_nms_sort(dets, nboxes, l.classes, nms);
        else diounms_sort(dets, nboxes, l.classes, nms, l.nms_kind, l.beta_nms);
    }
    //end = what_time_is_it();
    //spent_time += (end - start);
    //counter += 1;
    //printf("%lf ms\n", spent_time / counter * 1000);
    free_image(sized);
    return (detections){nboxes, dets};
}

int_pair get_model_input_shape(network* net) {
    int_pair shape = {net->w, net->h};
    return shape;
}

