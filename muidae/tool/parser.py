# parse command line argument and return args object

import argparse

def parse():

    parser = argparse.ArgumentParser()

    parser.add_argument('--nb_epoch', type=int, default=300, help='Number of epochs to train for')
    parser.add_argument('--dataset', type=str, default="100k", help='Dataset you are using')
    parser.add_argument('--batch_size', type=int, default=8, help='Number of images in each batch')
    parser.add_argument('--model', type=str, default="muidae", help='The model you are using')
    parser.add_argument('--learning_rate', type=float, default=0.00001, help='The learning rate')
    parser.add_argument('--regularization', type=float, default=0.01, help='The regularization parameter')
    parser.add_argument('--nb_layer', type=int, default=2, help='Number of encoding (or decoding) layer')
    parser.add_argument('--redux', type=float, default=1.0, help='Dataset reduction factor')
    parser.add_argument('--view', type=str, default='user_view', help='The view of the dataset ("user_view" or "item_view")')
    parser.add_argument('--zsize', type=int, default=16, help='Number of neurons in the middle layer')
    parser.add_argument('--reload_dataset', type=bool, default=False, help='Completely reload (and rewrite as binary) the dataset or not')
    parser.add_argument('--debug', help='Display debugging information.', action="store_true")
    parser.add_argument('--normalize', help='Remove global, user, and item mean from dataset.', action="store_true")

    args = parser.parse_args()

    return args