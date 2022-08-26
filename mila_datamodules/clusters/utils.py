"""Set of functions for creating torchvision datasets when on the Mila cluster.

IDEA: later on, we could also add some functions for loading torchvision models from a cached
directory.
"""
from __future__ import annotations

import functools
import inspect
import os
import shutil
import socket
from logging import getLogger as get_logger
from pathlib import Path
from typing import Callable, Sequence, TypeVar

import torchvision.datasets as tvd
from torch.utils.data import Dataset
from torchvision.datasets import VisionDataset
from typing_extensions import ParamSpec

D = TypeVar("D", bound=Dataset)
VD = TypeVar("VD", bound=VisionDataset)
P = ParamSpec("P")
C = Callable[P, D]

logger = get_logger(__name__)


def on_login_node() -> bool:
    # IDEA: Detect if we're on a login node somehow.
    return socket.getfqdn().endswith(".server.mila.quebec") and "SLURM_TMPDIR" not in os.environ


if "SLURM_TMPDIR" not in os.environ:
    raise RuntimeError(
        "You don't appear to have the SLURM environment variables set up. "
        "Perhaps you are on a login node, or are using the integrated terminal of VSCode through "
        "`mila code`, in which case you'd want to run the following command: "
        "`srun --pty /bin/bash`"
    )

SCRATCH: Path = Path(os.environ["SCRATCH"])
SLURM_TMPDIR: Path = Path(os.environ["SLURM_TMPDIR"])

dataset_files = {
    tvd.MNIST: ["MNIST"],
    tvd.CIFAR10: ["cifar-10-batches-py"],
    tvd.CIFAR100: ["cifar-100-python"],
}
""" a map of the files needed for each dataset type, relative to the `root_dir`.

These are the files which would be normally downloaded into `root_dir` when calling
`Dataset(root_dir, download=True)`.
"""


def all_files_exist(
    required_files: Sequence[str],
    base_dir: Path,
) -> bool:
    return all((base_dir / f).exists() for f in required_files)


def replace_kwargs(dataset_type: Callable[P, D], **fixed_arguments) -> Callable[P, D]:
    """Returns a callable where the given argument values are fixed.

    NOTE: Simply using functools.partial wouldn't work, since passing one of the fixed arguments
    would raise an error.
    """
    init_signature = inspect.signature(dataset_type)

    @functools.wraps(dataset_type)
    def _wrap(*args: P.args, **kwargs: P.kwargs) -> D:
        bound_signature = init_signature.bind_partial(*args, **kwargs)
        for key, value in fixed_arguments.items():
            bound_signature.arguments[key] = value
        args = bound_signature.args  # type: ignore
        kwargs = bound_signature.kwargs  # type: ignore
        return dataset_type(*args, **kwargs)

    return _wrap


def copy_dataset_files(files_to_copy: Sequence[str], source_dir: Path, dest_dir: Path) -> None:
    assert all_files_exist(files_to_copy, base_dir=source_dir)
    for source_file in files_to_copy:
        source_path = source_dir / source_file
        destination_path = dest_dir / source_file
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Copying {source_path} -> {destination_path}")
        if source_path.is_dir():
            # Copy the folder over.
            # TODO: Check that this doesn't overwrite existing files.
            # TODO: Test this out with symlinks?
            shutil.copytree(
                src=source_path,
                dst=destination_path,
                symlinks=False,
                dirs_exist_ok=True,
            )
        elif not destination_path.exists():
            # Copy the file over.
            shutil.copy(src=source_path, dst=destination_path, follow_symlinks=False)