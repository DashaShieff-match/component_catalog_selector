from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .metadata import CATEGORY_METADATA, CATEGORY_ORDER, category_sort_key
from .models import Component, SelectionCriteria
from .widgets import ScrollableFrame


class SubsetStageMixin:
    EXPECTED_COMPONENT_COUNT = 39

    def _build_subset_stage(self) -> None:
        self._clear_main_frame()
        self.category_vars = {}
        if not self.data_type_vars:
            self.data_type_vars = {
                "step": tk.BooleanVar(value=True),
                "stl": tk.BooleanVar(value=False),
            }

        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_rowconfigure(3, weight=0)
        self.main_frame.grid_rowconfigure(4, weight=0)

        header = ttk.Frame(self.main_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ttk.Label(header, text="Stage 1: Catalog subset", font=("", 16, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(header, text=self._catalog_status_text()).grid(row=1, column=0, sticky="w", pady=(4, 0))
        ttk.Label(
            header,
            text="Select the categories you want to include in the validation set from the overall catalog.",
            foreground="#555555",
            wraplength=760,
        ).grid(row=2, column=0, sticky="w", pady=(4, 0))

        button_bar = ttk.Frame(header)
        button_bar.grid(row=0, column=1, rowspan=3, sticky="e")
        ttk.Button(button_bar, text="Select all", command=lambda: self._set_all_subset_values(True)).grid(
            row=0,
            column=0,
            padx=(0, 8),
        )
        ttk.Button(button_bar, text="Clear", command=lambda: self._set_all_subset_values(False)).grid(row=0, column=1)

        data_type_frame = ttk.LabelFrame(self.main_frame, text="Data type", padding=10)
        data_type_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        ttk.Checkbutton(
            data_type_frame,
            text="STEP",
            variable=self.data_type_vars["step"],
            command=self._update_selected_count,
        ).grid(row=0, column=0, sticky="w", padx=(0, 18))
        ttk.Checkbutton(
            data_type_frame,
            text="STL",
            variable=self.data_type_vars["stl"],
            command=self._update_selected_count,
        ).grid(row=0, column=1, sticky="w")

        scrollable = ScrollableFrame(self.main_frame)
        scrollable.grid(row=2, column=0, sticky="nsew")
        scrollable.content.grid_columnconfigure(0, weight=1)
        scrollable.content.grid_columnconfigure(1, weight=1)

        values_by_category = self.catalog.values_by_category()
        for index, category in enumerate(CATEGORY_ORDER):
            category_frame = ttk.LabelFrame(scrollable.content, text=CATEGORY_METADATA[category].title, padding=10)
            category_frame.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=(0 if index % 2 == 0 else 8, 0 if index % 2 == 1 else 8),
                pady=8,
            )
            category_frame.grid_columnconfigure(0, weight=1)
            self._build_subset_category(category_frame, category, values_by_category[category])

        footer = ttk.Frame(self.main_frame)
        footer.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        footer.grid_columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.selected_count_var).grid(row=0, column=0, sticky="w")
        ttk.Button(footer, text="Confirm subset", command=self._confirm_subset).grid(row=0, column=1, sticky="e")
        self._update_selected_count()

    def _build_subset_category(self, frame: ttk.LabelFrame, category: str, values: set[str]) -> None:
        self.category_vars[category] = {}
        sorted_values = sorted(values, key=lambda code: category_sort_key(category, code))
        for row_index, code in enumerate(sorted_values):
            var = tk.BooleanVar(value=True)
            self.category_vars[category][code] = var
            ttk.Checkbutton(
                frame,
                text=self._checkbox_label(category, code, self.catalog.components),
                variable=var,
                command=self._update_selected_count,
            ).grid(row=row_index, column=0, sticky="w", pady=2)

    def _catalog_status_text(self) -> str:
        step_component_ids = {component.component_id for component in self.catalog.components}
        stl_component_ids = self._catalog_file_ids(self.stl_catalog_dir, ".stl")
        loaded_count = len(step_component_ids & stl_component_ids)

        text = (
            f"Loaded {loaded_count} STEP and STL files. "
            f"STEP folder: {self._catalog_folder_status(self.catalog_dir, step_component_ids)}; "
            f"STL folder: {self._catalog_folder_status(self.stl_catalog_dir, stl_component_ids)}"
        )
        if self.catalog.ignored_non_step_files:
            ignored_names = ", ".join(path.name for path in self.catalog.ignored_non_step_files)
            text += f"; ignored non-STEP files: {ignored_names}"
        if self.catalog.ignored_unparsed_step_files:
            ignored_names = ", ".join(path.name for path in self.catalog.ignored_unparsed_step_files)
            text += f"; ignored unparsed STEP files: {ignored_names}"
        return text

    def _catalog_folder_status(self, folder: Path, component_ids: set[str]) -> str:
        if not folder.exists():
            return "Error! Folder not found."
        if not self._is_full_catalog_loaded(component_ids):
            return "Error! Full catalog not present."
        return str(folder.relative_to(self.project_root))

    def _is_full_catalog_loaded(self, component_ids: set[str]) -> bool:
        if len(component_ids) != self.EXPECTED_COMPONENT_COUNT:
            return False

        step_component_ids = {component.component_id for component in self.catalog.components}
        if len(step_component_ids) != self.EXPECTED_COMPONENT_COUNT:
            return True
        return component_ids == step_component_ids

    def _catalog_file_ids(self, folder: Path, extension: str) -> set[str]:
        if not folder.exists():
            return set()
        return {
            path.stem
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() == extension
        }

    def _checkbox_label(self, category: str, code: str, components: list[Component]) -> str:
        label = CATEGORY_METADATA[category].label_for(code)
        count = sum(1 for component in components if component.value_for(category) == code)
        return f"{code} - {label} ({count})"

    def _set_all_subset_values(self, value: bool) -> None:
        for category_vars in self.category_vars.values():
            for var in category_vars.values():
                var.set(value)
        self._update_selected_count()

    def _selected_data_types(self) -> set[str]:
        return {data_type for data_type, var in self.data_type_vars.items() if var.get()}

    def _selected_criteria(self) -> SelectionCriteria:
        allowed_values = {
            category: {code for code, var in code_vars.items() if var.get()}
            for category, code_vars in self.category_vars.items()
        }
        return SelectionCriteria(allowed_values=allowed_values)

    def _selected_subset(self) -> list[Component]:
        return self._selected_criteria().filter_components(self.catalog.components)

    def _update_selected_count(self) -> None:
        selected_count = len(self._selected_subset())
        selected_types = ", ".join(data_type.upper() for data_type in sorted(self._selected_data_types()))
        if not selected_types:
            selected_types = "none"
        self.selected_count_var.set(f"Selected subset: {selected_count} component(s); data type(s): {selected_types}")

    def _confirm_subset(self) -> None:
        if not self._selected_data_types():
            messagebox.showerror("No data type selected", "Select at least one data type: STEP, STL, or both.")
            return

        empty_categories = [
            CATEGORY_METADATA[category].title
            for category, code_vars in self.category_vars.items()
            if not any(var.get() for var in code_vars.values())
        ]
        if empty_categories:
            messagebox.showerror("Subset incomplete", "Select at least one value for: " + ", ".join(empty_categories))
            return

        self.selected_components = self._selected_subset()
        if not self.selected_components:
            messagebox.showerror("No components selected", "The selected category filters contain no STEP files.")
            return

        self.confirmed_generalization_categories = set()
        self.confirmed_generalization_test_values = {}
        self._build_generalization_stage()
