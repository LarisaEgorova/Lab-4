"""Лабораторная работа №4 — задача Дирихле для уравнения Пуассона (вариант 2).

Графический интерфейс: выбор метода и задачи, настройка параметров,
вывод таблиц расчётов и поверхностей. Вычисления выполняет ядро на C++.
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.append(os.path.join(ROOT, "python"))

import matplotlib
matplotlib.use("TkAgg")
matplotlib.rcParams["figure.dpi"] = 130
matplotlib.rcParams["figure.autolayout"] = True
matplotlib.rcParams["font.size"] = 10
matplotlib.rcParams["lines.antialiased"] = True

import core_runner as cr
import convergence as conv

from gui_widgets import apply_theme, LoadingDialog, COLORS
from gui_panels import ParamPanel, ResultView
import gui_help

class PoissonApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа №4 — задача Дирихле "
                   "для уравнения Пуассона (вариант 2)")
        self.geometry("1340x920")
        self.minsize(1120, 740)

        apply_theme(self)
        self._build_menu()

        self.panel = ParamPanel(self, on_run=self.run_calculation)
        self.panel.pack(side=tk.LEFT, fill=tk.Y)

        right = tk.Frame(self, background=COLORS["bg"])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.view = ResultView(self, right)
        self.view.placeholder()

    def _build_menu(self):
        menubar = tk.Menu(self)
        m = tk.Menu(menubar, tearoff=0)
        m.add_command(label="Справка по лабораторной",
                      command=lambda: gui_help.show_help_window(self))
        m.add_separator()
        m.add_command(label="О программе", command=self._about)
        menubar.add_cascade(label="Помощь", menu=m)
        self.config(menu=menubar)

    def _about(self):
        messagebox.showinfo(
            "О программе",
            "Лабораторная работа №4, вариант 2.\n"
            "Задача Дирихле для уравнения Пуассона.\n\n"
            "Вычислительное ядро: C++ (метод Зейделя и МВР).\n"
            "Интерфейс и графика: Python (tkinter, matplotlib).")

    def run_calculation(self):
        try:
            params = self.panel.collect()
        except ValueError as e:
            messagebox.showerror("Проверьте параметры", str(e))
            return
        self.panel.btn_run.config(state=tk.DISABLED)

        self.loading = LoadingDialog(self, on_cancel=cr.cancel_active_process)
        threading.Thread(target=self._worker, args=(params,), daemon=True).start()

    def _worker(self, params):
        try:
            self.after(0, lambda: self.loading.set_status("Компиляция ядра при первом запуске..."))
            cr.compile_core()
            self.after(0, lambda: self.loading.set_status("Решение системы итерационным методом..."))

            def update_progress(iters, cur_eps):
                msg = f"Итерация {iters}, текущая невязка ≈ {cur_eps:.2e}"
                self.after(0, lambda: self.loading.set_status(msg))

            d = cr.run_solver(
                params["problem"], params["method"], params["n"], params["m"],
                omega=params["omega"], eps=params["eps"], nmax=params["nmax"],
                interp=params["interp"], grids=True, stride=1,
                progress_cb=update_progress
            )

            conv_rows = None
            if params["conv"]:
                self.after(0, lambda: self.loading.set_status("Оценка порядка сходимости (вычисление серии)..."))
                if params["problem"] == "test":
                    conv_rows = conv.convergence_test(params["method"])
                else:
                    conv_rows = conv.convergence_main(params["method"])

            self.after(0, self._done, d, conv_rows)

        except InterruptedError as exc:
            self.after(0, self._cancelled, str(exc))
        except Exception as exc:
            self.after(0, self._error, exc)

    def _done(self, d, conv_rows):
        self.loading.finish()
        self.panel.btn_run.config(state=tk.NORMAL)
        self.view.render(d, conv_rows)

    def _cancelled(self, msg):
        self.loading.finish()
        self.panel.btn_run.config(state=tk.NORMAL)

    def _error(self, exc):
        self.loading.finish()
        self.panel.btn_run.config(state=tk.NORMAL)
        messagebox.showerror("Ошибка расчёта", str(exc))

def main():
    PoissonApp().mainloop()

if __name__ == "__main__":
    main()
