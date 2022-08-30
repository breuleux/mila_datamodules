from __future__ import annotations

import shutil
from pathlib import Path
from typing import Callable

from pl_bolts.datamodules import CityscapesDataModule as _CityscapesDataModule
from torch import nn

from mila_datamodules.clusters import CURRENT_CLUSTER, SLURM_TMPDIR
from mila_datamodules.clusters.cluster_enum import ClusterType

from .vision_datamodule import _TransformsFix

# TODO: Add for other clusters!
# TODO: Copy the archive and use the script to recreate the dataset in SLURM_TMPDIR.
cityscapes_dir_locations = {
    ClusterType.MILA: "/network/datasets/cityscapes.var/cityscapes_torchvision",
}


class CityscapesDataModule(_CityscapesDataModule, _TransformsFix):
    def __init__(
        self,
        data_dir: str | None = None,
        quality_mode: str = "fine",
        target_type: str = "instance",
        num_workers: int = 0,
        batch_size: int = 32,
        seed: int = 42,
        shuffle: bool = True,
        pin_memory: bool = True,
        drop_last: bool = False,
        train_transforms: Callable | nn.Module | None = None,
        val_transforms: Callable | nn.Module | None = None,
        test_transforms: Callable | nn.Module | None = None,
    ) -> None:
        data_dir = str(SLURM_TMPDIR / "cityscapes")
        super().__init__(
            data_dir=data_dir,
            quality_mode=quality_mode,
            target_type=target_type,
            num_workers=num_workers,
            batch_size=batch_size,
            seed=seed,
            shuffle=shuffle,
            pin_memory=pin_memory,
            drop_last=drop_last,
            train_transforms=train_transforms,
            val_transforms=val_transforms,
            test_transforms=test_transforms,
        )

    def prepare_data(self):
        cityscapes_dir_location = cityscapes_dir_locations.get(CURRENT_CLUSTER)
        if cityscapes_dir_location is None:
            raise NotImplementedError(
                f"Don't know where cityscapes data is located in cluster {ClusterType.current()}"
            )

        done_file = Path(self.data_dir) / "done.txt"
        if not done_file.exists():
            print(f"Copying cityscapes data from {cityscapes_dir_location} to {self.data_dir}")
            shutil.copytree(cityscapes_dir_location, self.data_dir, dirs_exist_ok=True)
            done_file.touch()
        super().prepare_data()
