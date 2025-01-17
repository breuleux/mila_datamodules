"""Tests that ensure that the information in the registry is correct.

1. Make sure that the files for each dataset are available in the clusters.
2. Checks that these files are sufficient to instantiate the datasets.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from typing import Callable, TypeVar

import pytest
from torch.utils.data import Dataset
from typing_extensions import ParamSpec

from mila_datamodules.clusters import Cluster
from mila_datamodules.testutils import param_only_runs_on_cluster
from mila_datamodules.utils import all_files_exist

from .registry import (
    _dataset_files,
    dataset_archives_locations_per_cluster,
    dataset_roots_per_cluster,
    is_stored_on_cluster,
    locate_dataset_root_on_cluster,
)

P = ParamSpec("P")
D = TypeVar("D", bound=Dataset)


def check_dataset_creation_works_without_download(
    dataset_type: Callable[P, D],
    *args: P.args,
    **kwargs: P.kwargs,
) -> D:
    """Utility function that creates the dataset with the given kwargs (and with
    download=False)."""
    if "download" in kwargs or "download" in inspect.signature(dataset_type).parameters:
        kwargs["download"] = False
    return check_dataset_creation_works(dataset_type, *args, **kwargs)


def check_dataset_creation_works(
    dataset_type: Callable[P, D],
    download: bool = False,
    *args: P.args,
    **kwargs: P.kwargs,
) -> D:
    """Utility function that creates the dataset with the given args and checks that it 'works'."""
    assert not download
    dataset = dataset_type(*args, **kwargs)
    length = len(dataset)  # type: ignore
    assert length > 0
    _ = dataset[0]
    _ = dataset[length // 2]
    _ = dataset[length - 1]
    return dataset


@pytest.mark.parametrize(
    "cluster,dataset",
    [
        param_only_runs_on_cluster(cluster, dataset_cls, cluster=cluster)
        for cluster, dataset_cls_to_root in dataset_roots_per_cluster.items()
        for dataset_cls in dataset_cls_to_root
    ],
)
def test_dataset_files_in_registry_are_actually_there(cluster: Cluster, dataset: type[Dataset]):
    """Test that the files associated with the dataset class are actually present in the `root` of
    that dataset, if supported on the current cluster."""
    assert is_stored_on_cluster(dataset, cluster=cluster)

    # TODO: This is actually a little wrong.
    # if it's stored in an extracted form, then check that all the files exist.

    # Cluster has this dataset (or so it says). Check that all the required files are there.
    root = locate_dataset_root_on_cluster(dataset, cluster=cluster)
    # Assert that we know which files are required in order to load this dataset.
    # NOTE: These are the files which would get copied if we wanted to copy the dataset to the fast
    # directory.

    assert dataset in _dataset_files
    required_files = _dataset_files[dataset]
    assert all_files_exist(required_files, root)


@pytest.mark.parametrize(
    "cluster,dataset",
    [
        param_only_runs_on_cluster(cluster, dataset_cls, cluster=cluster)
        for cluster, dataset_cls_to_archives in dataset_archives_locations_per_cluster.items()
        for dataset_cls in dataset_cls_to_archives
    ],
)
def test_dataset_archives_in_registry_are_actually_there(cluster: Cluster, dataset: type[Dataset]):
    """Test that the archives associated with the dataset class are actually present on the
    cluster."""
    archives = dataset_archives_locations_per_cluster[cluster][dataset]
    assert all(Path(archive_file).exists() for archive_file in archives)
    for archive_file in archives:
        from gzip import GzipFile
        from tarfile import TarFile
        from zipfile import ZipFile

        if archive_file.endswith(".tar.gz"):
            with GzipFile(archive_file, "rb") as f:
                with TarFile(fileobj=f) as tar:
                    assert False, tar.getmembers()
        elif archive_file.endswith(".tar"):
            with TarFile(archive_file, "r") as tar:
                assert False, tar.getmembers()
        elif archive_file.endswith(".zip"):
            with ZipFile(archive_file, "r") as zip:
                assert False, zip.namelist()
        assert Path(archive_file).exists()
    raise NotImplementedError("TODO")


# NOTE: Commenting these out. Created some dedicated test classes for each in `datasets_tests.py`
# Datasets that only have `root` as a required parameter.
# easy_to_use_datasets = [
#     dataset
#     for dataset in vars(torchvision.datasets).values()
#     if inspect.isclass(dataset)
#     and dataset is not torchvision.datasets.VisionDataset
#     and not any(
#         n != "root" and p.default is p.empty
#         for n, p in inspect.signature(dataset).parameters.items()
#     )
# ]

# easy_to_use_datasets = [
#     pytest.param(dataset, marks=xfail_if_not_stored_on_current_cluster(dataset))
#     for dataset in easy_to_use_datasets
# ]


# @pytest.mark.parametrize("dataset", easy_to_use_datasets)
# def test_dataset_creation(dataset: type[Dataset]):
#     """Test creating the torchvision datasets that don't have any other required arguments besides
#     'root', using the root that we get from `get_dataset_root`."""
#     check_dataset_creation_works_without_download(
#         dataset,
#         root=locate_dataset_root_on_cluster(dataset, default="/network/datasets/torchvision"),
#     )
