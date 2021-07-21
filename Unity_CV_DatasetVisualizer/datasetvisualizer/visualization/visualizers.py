﻿from pathlib import Path
import numpy as np
import PIL

from datasetinsights.datasets.unity_perception import AnnotationDefinitions
from datasetinsights.datasets.unity_perception.captures import Captures
from datasetinsights.datasets.synthetic import read_bounding_box_2d, read_bounding_box_3d
from datasetinsights.stats.visualization.plots import plot_bboxes, plot_bboxes3d, plot_keypoints

from PIL.Image import Image


def cleanup(catalog, data_root):
    catalog = remove_captures_with_missing_files(data_root, catalog)
    # catalog = remove_captures_without_bboxes(catalog)
    return catalog


def remove_captures_without_bboxes(catalog):
    keep_mask = catalog["annotation.values"].apply(len) > 0
    return catalog[keep_mask]


def remove_captures_with_missing_files(root, catalog):
    def exists(capture_file):
        path = Path(root) / capture_file
        return path.exists()

    keep_mask = catalog.filename.apply(exists)
    return catalog[keep_mask]


def capture_df(def_id, data_root):
    captures = Captures(data_root)
    catalog = captures.filter(def_id)
    catalog = cleanup(catalog, data_root)
    return catalog


def label_mappings_dict(def_id, data_root):
    annotation_def = AnnotationDefinitions(data_root)
    init_definition = annotation_def.get_definition(def_id)
    label_mappings = {
        m["label_id"]: m["label_name"] for m in init_definition["spec"]
    }
    return label_mappings


def draw_image_with_boxes(
    image,
    index,
    catalog,
    label_mappings,
):
    cap = catalog.iloc[index]
    ann = cap["annotation.values"]
    capture = image
    image = capture.convert("RGB")  # Remove alpha channel
    bboxes = read_bounding_box_2d(ann, label_mappings)
    return plot_bboxes(image, bboxes, label_mappings)


def draw_image_with_segmentation(
    image: Image,
    segmentation: Image,
):
    """
    Draws an image in streamlit with labels and bounding boxes.

    :param image: the PIL image
    :type PIL:
    :param height: height of the image
    :type int:
    :param width: width of the image
    :type int:
    :param segmentation: Segmentation Image
    :type PIL:
    :param header: Image header
    :type str:
    :param description: Image description
    :type str:
    """
    # image_draw = ImageDraw(segmentation)
    rgba = np.array(segmentation.copy().convert("RGBA"))
    r, g, b, a = rgba.T
    black_areas = (r == 0) & (b == 0) & (g == 0) & (a == 255)
    other_areas = (r != 0) | (b != 0) | (g != 0)
    rgba[..., 0:4][black_areas.T] = (0, 0, 0, 0)
    rgba[..., -1][other_areas.T] = int(0.6 * 255)

    foreground = PIL.Image.fromarray(rgba)
    image = image.copy()
    image.paste(foreground, (0, 0), foreground)
    return image


def find_metadata_annotation_index(dataset, name):
    for idx, annotation in enumerate(dataset.metadata.annotations):
        if annotation["name"] == name:
            return idx


def draw_image_with_keypoints(
    image, annotations, templates
):
    return plot_keypoints(image, annotations, templates)


#TODO Implement colors
def draw_image_with_box_3d(image, sensor, values, colors):
    if 'camera_intrinsic' in sensor:
        projection = np.array(sensor["camera_intrinsic"])
    else:
        projection = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    boxes = read_bounding_box_3d(values)
    img_with_boxes = plot_bboxes3d(image, boxes, projection, None,
                                   orthographic=(sensor["projection"] == "orthographic"))
    return img_with_boxes
