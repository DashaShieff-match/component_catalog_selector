from __future__ import annotations

import sys
from pathlib import Path
from tkinter import messagebox

from component_selector.app import ComponentSelectorApp


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main() -> None:
    try:
        app = ComponentSelectorApp(project_root=project_root())
    except FileNotFoundError as error:
        messagebox.showerror("Catalog not found", str(error))
        return

    app.mainloop()


if __name__ == "__main__":
    main()
