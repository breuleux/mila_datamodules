"""Script to check which `VisionDataset`s work out-of-the-box on the current cluster."""

import json
from collections import defaultdict

import cv2  # noqa
from torchvision.datasets import VisionDataset

from mila_datamodules.registry import locate_dataset_root_on_cluster

successes = []
failures = defaultdict(list)
for dataset_class in VisionDataset.__subclasses__():
    k = dataset_class.__qualname__
    print(k)
    try:
        dataset_root = locate_dataset_root_on_cluster(dataset_class)
        dataset = dataset_class(str(dataset_root))
    except Exception as err:
        exception_str = f"{type(err).__name__}('{err}')"
        failures[exception_str].append(dataset_class)
    else:
        print(f"Success for {k}")
        successes.append(dataset_class)

print("Successes:", successes)

print("Failures:")
print(
    json.dumps(
        {k: [v.__qualname__ for v in vs] for k, vs in failures.items()},
        indent="\t",
    )
)

FAILURES_MILA = """{
    TypeError("Can't instantiate abstract class FlowDataset with abstract method _read_flow"): [
        "FlowDataset"
    ],
    RuntimeError("Dataset not found or corrupted. You can use download=True to download it"): [
        "CLEVRClassification",
        "Flowers102",
        "Omniglot",
        "_VOCBase",
    ],
    TypeError("__init__() missing 1 required positional argument: 'annFile'"): [tvd.CocoDetection],
    TypeError("__init__() missing 1 required positional argument: 'loader'"): ["DatasetFolder"],
    RuntimeError("Dataset not found. You can use download=True to download it"): [
        "DTD",
        "FGVCAircraft",
        "Food101",
        "GTSRB",
        "OxfordIIITPet",
        "RenderedSST2",
        "StanfordCars",
        "SUN397",
    ],
    RuntimeError(
        "train.csv not found in /network/datasets/torchvision/fer2013 or corrupted. You can download it from https://www.kaggle.com/c/challenges-in-representation-learning-facial-expression-recognition-challenge"
    ): ["FER2013"],
    TypeError("__init__() missing 1 required positional argument: 'ann_file'"): [
        "Flickr8k",
        "Flickr30k",
    ],
    TypeError(
        "__init__() missing 2 required positional arguments: 'annotation_path' and 'frames_per_clip'"
    ): [
        "HMDB51",
        "UCF101",
    ],
    TypeError("__init__() missing 1 required positional argument: 'frames_per_clip'"): [
        "Kinetics"
    ],
    RuntimeError("Dataset not found. You may use download=True to download it."): ["Kitti"],
    TypeError(
        "__init__() missing 3 required positional arguments: 'split', 'image_set', and 'view'"
    ): ["_LFW"],
    ModuleNotFoundError("No module named 'lmdb'"): ["LSUNClass", "LSUN"],
    RuntimeError(
        "h5py is not found. This dataset needs to have h5py installed: please run pip install h5py"
    ): ["PCAM"],
    TypeError("__init__() missing 1 required positional argument: 'name'"): ["PhotoTour"],
    FileNotFoundError(
        "[Errno 2] No such file or directory: '/network/datasets/torchvision/train.txt'"
    ): ["SBDataset"],
    HTTPError("HTTP Error 403: Forbidden"): ["SBU"],
    OSError("[Errno 30] Read-only file system: '/network/datasets/torchvision/semeion.data'"): [
        "SEMEION"
    ],
    FileNotFoundError(
        "[Errno 2] No such file or directory: '/network/datasets/torchvision/usps.bz2'"
    ): ["USPS"],
    RuntimeError(
        "Dataset not found or corrupted. You can use download=True to download and prepare it"
    ): ["WIDERFace"],
}
"""
