"""Вспомогательные элементы интерфейса: цветовая тема и индикатор загрузки."""
import tkinter as tk
from tkinter import ttk

COLORS = {
    "bg":       "#f4f7fb",
    "panel":    "#e9f0fb",
    "card":     "#ffffff",
    "accent":   "#2f6fed",
    "accent2":  "#7c4dff",
    "ok":       "#1faa59",
    "text":     "#1b2733",
    "muted":    "#5a6b7b",
    "heading":  "#143a8a",
}

def apply_theme(root):
    """Настроить ttk-стиль приложения в ярких тонах."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    c = COLORS
    root.configure(background=c["bg"])

    style.configure(".", background=c["bg"], foreground=c["text"],
                    font=("Segoe UI", 10))
    style.configure("TFrame", background=c["bg"])
    style.configure("Panel.TFrame", background=c["panel"])
    style.configure("TLabel", background=c["bg"], foreground=c["text"])
    style.configure("Panel.TLabel", background=c["panel"], foreground=c["text"])
    style.configure("Header.TLabel", font=("Segoe UI", 11, "bold"),
                    foreground=c["heading"], background=c["panel"])
    style.configure("Title.TLabel", font=("Segoe UI", 13, "bold"),
                    foreground=c["heading"], background=c["bg"])

    style.configure("TRadiobutton", background=c["panel"], foreground=c["text"])
    style.configure("TCheckbutton", background=c["panel"], foreground=c["text"])
    style.map("TRadiobutton", background=[("active", c["panel"])])
    style.map("TCheckbutton", background=[("active", c["panel"])])

    style.configure("TButton", font=("Segoe UI", 10), padding=4)
    style.configure("Run.TButton", font=("Segoe UI", 12, "bold"),
                    foreground="#ffffff", background=c["accent"], padding=8)
    style.map("Run.TButton",
              background=[("active", c["accent2"]), ("disabled", "#9bb4e8")])
    style.configure("Grid.TButton", font=("Segoe UI", 9), padding=2)

    style.configure("Card.TLabelframe", background=c["panel"],
                    bordercolor=c["accent"], relief="solid", borderwidth=1)
    style.configure("Card.TLabelframe.Label", font=("Segoe UI", 10, "bold"),
                    foreground=c["accent"], background=c["panel"])

    style.configure("Treeview", rowheight=24, font=("Consolas", 10),
                    fieldbackground=c["card"], background=c["card"])
    style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                    background=c["accent"], foreground="#ffffff")
    style.map("Treeview", background=[("selected", "#cfe0ff")])

    style.configure("TNotebook", background=c["bg"])
    style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(14, 6))
    style.map("TNotebook.Tab",
              background=[("selected", c["card"])],
              foreground=[("selected", c["heading"])])

    style.configure("Accent.Horizontal.TProgressbar",
                    background=c["accent"], troughcolor=c["panel"])
    return style

class LoadingDialog(tk.Toplevel):
    """Небольшое модальное окно с индикатором выполнения расчёта и кнопкой отмены."""
    def __init__(self, parent, on_cancel=None):
        super().__init__(parent)
        self.on_cancel = on_cancel
        self.title("Расчёт")
        self.resizable(False, False)
        self.transient(parent)
        self.configure(padx=26, pady=22, background=COLORS["card"])

        tk.Label(self, text="Выполняется расчёт", font=("Segoe UI", 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["heading"]).pack(pady=(0, 12))

        self.bar = ttk.Progressbar(self, mode="indeterminate", length=300,
                                   style="Accent.Horizontal.TProgressbar")
        self.bar.pack()
        self.bar.start(15)

        self.status = tk.Label(self, text="Подготовка ядра и сетки...",
                               font=("Segoe UI", 9), bg=COLORS["card"], fg=COLORS["muted"])
        self.status.pack(pady=(10, 8))

        ttk.Button(self, text="Прервать расчёт", command=self.cancel_action).pack()

        self.protocol("WM_DELETE_WINDOW", self.cancel_action)

        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width() // 2 - self.winfo_width() // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{px}+{py}")
        self.grab_set()

    def set_status(self, msg):
        self.status.config(text=msg)

    def cancel_action(self):
        self.set_status("Отмена операции, подождите...")
        self.bar.stop()
        if self.on_cancel:
            self.on_cancel()

    def finish(self):
        self.bar.stop()
        self.grab_release()
        self.destroy()