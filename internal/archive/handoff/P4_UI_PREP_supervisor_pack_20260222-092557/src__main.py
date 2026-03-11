import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import flet as ft

from src.ui.main_window import main


if __name__ == "__main__":
    print("[WINDBG] launching app")
    ft.run(main, view=ft.AppView.FLET_APP)


