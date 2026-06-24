from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from .models import Component, CopyResult, SplitResult


class ComponentFileCopier:
    TRAIN_DIR_NAME = "DevelopmentSet"
    TEST_DIR_NAME = "ValidationSet"
    DATA_TYPE_EXTENSIONS = {
        "step": ".STEP",
        "stl": ".STL",
    }

    def __init__(self, output_root: Path, step_catalog_dir: Path, stl_catalog_dir: Path) -> None:
        self.output_root = output_root
        self.catalog_dirs = {
            "step": step_catalog_dir,
            "stl": stl_catalog_dir,
        }

    def copy_split(
        self,
        split_result: SplitResult,
        clear_existing_files: bool,
        selected_data_types: set[str],
    ) -> CopyResult:
        train_dir = self.output_root / self.TRAIN_DIR_NAME
        test_dir = self.output_root / self.TEST_DIR_NAME

        train_dir.mkdir(exist_ok=True)
        test_dir.mkdir(exist_ok=True)

        selected_data_types = set(selected_data_types)
        self._validate_selected_data_types(selected_data_types)

        if clear_existing_files:
            self._clear_files(train_dir)
            self._clear_files(test_dir)

        train_file_count = self._copy_components(split_result.train_components, train_dir, selected_data_types)
        test_file_count = self._copy_components(split_result.test_components, test_dir, selected_data_types)

        return CopyResult(
            train_dir=train_dir,
            test_dir=test_dir,
            train_count=len(split_result.train_components),
            test_count=len(split_result.test_components),
            train_file_count=train_file_count,
            test_file_count=test_file_count,
            selected_data_types=selected_data_types,
        )

    def _validate_selected_data_types(self, selected_data_types: set[str]) -> None:
        if not selected_data_types:
            raise ValueError("Select at least one data type to copy.")

        unknown_data_types = selected_data_types - set(self.DATA_TYPE_EXTENSIONS)
        if unknown_data_types:
            raise ValueError("Unknown data type(s): " + ", ".join(sorted(unknown_data_types)))

    def _clear_files(self, folder: Path) -> None:
        selected_extensions = {extension.lower() for extension in self.DATA_TYPE_EXTENSIONS.values()}
        for path in folder.iterdir():
            if path.is_file() and path.suffix.lower() in selected_extensions:
                path.unlink()

    def _copy_components(
        self,
        components: Iterable[Component],
        destination_dir: Path,
        selected_data_types: set[str],
    ) -> int:
        copied_count = 0
        for component in components:
            for source_path in self._source_paths(component, selected_data_types):
                shutil.copy2(source_path, destination_dir / source_path.name)
                copied_count += 1
        return copied_count

    def _source_paths(self, component: Component, selected_data_types: set[str]) -> list[Path]:
        source_paths: list[Path] = []
        for data_type in sorted(selected_data_types):
            source_path = (
                self.catalog_dirs[data_type]
                / f"{component.component_id}{self.DATA_TYPE_EXTENSIONS[data_type]}"
            )
            if not source_path.exists():
                raise FileNotFoundError(f"Missing {data_type.upper()} file for {component.component_id}: {source_path}")
            source_paths.append(source_path)
        return source_paths
