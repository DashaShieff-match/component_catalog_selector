from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .catalog import CatalogScanner
from .file_copier import ComponentFileCopier
from .holdout_stage import HoldoutStageMixin
from .models import CatalogScanResult
from .output_mixin import OutputMixin
from .split_planner import SplitPlanner
from .split_settings_mixin import SplitSettingsMixin
from .split_stage import SplitStageMixin
from .subset_stage import SubsetStageMixin


class ComponentSelectorApp(
    SubsetStageMixin,
    HoldoutStageMixin,
    SplitStageMixin,
    SplitSettingsMixin,
    OutputMixin,
    tk.Tk,
):
    def __init__(self, project_root: Path) -> None:
        super().__init__()

        self.project_root = project_root
        self.catalog_dir = project_root / "FullCatalogSTEP"
        self.stl_catalog_dir = project_root / "FullCatalogSTL"
        self.catalog = self._scan_catalog()
        self.split_planner = SplitPlanner()
        self.file_copier = ComponentFileCopier(project_root, self.catalog_dir, self.stl_catalog_dir)

        self.category_vars: dict[str, dict[str, tk.BooleanVar]] = {}
        self.data_type_vars: dict[str, tk.BooleanVar] = {}
        self.generalization_test_value_vars: dict[str, dict[str, tk.BooleanVar]] = {}
        self.confirmed_generalization_categories: set[str] = set()
        self.confirmed_generalization_test_values: dict[str, set[str]] = {}
        self.selected_components = []

        self.selected_count_var = tk.StringVar()
        self.target_test_percent_var = tk.DoubleVar(value=30.0)
        self.target_test_percent_label_var = tk.StringVar(value="")
        self.actual_split_preview_var = tk.StringVar(value="")
        self.random_seed_var = tk.StringVar()
        self.clear_existing_var = tk.BooleanVar(value=True)
        self.output_text: tk.Text | None = None

        self.title("Component Development/Validation Selector")
        self.geometry("940x760")
        self.minsize(760, 560)

        self.main_frame = ttk.Frame(self, padding=16)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_subset_stage()

    def _clear_main_frame(self) -> None:
        for child in self.main_frame.winfo_children():
            child.destroy()
        self.output_text = None

    def _scan_catalog(self) -> CatalogScanResult:
        if not self.catalog_dir.exists():
            return CatalogScanResult(
                components=[],
                ignored_non_step_files=[],
                ignored_unparsed_step_files=[],
            )
        return CatalogScanner(self.catalog_dir).scan()
