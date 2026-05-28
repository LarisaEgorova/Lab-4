"""Панель параметров и область вывода результатов (вкладки: графики и таблицы)."""
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)

from gui_widgets import COLORS

EPS_TARGET = 0.5e-4

class ParamPanel(ttk.Frame):
    """Левая панель: выбор метода, задачи и всех параметров."""
    def __init__(self, parent, on_run):
        super().__init__(parent, style="Panel.TFrame", padding=14)
        self.on_run = on_run

        self.var_method = tk.StringVar(value="sor")
        self.var_problem = tk.StringVar(value="test")
        self.var_n = tk.IntVar(value=64)
        self.var_m = tk.IntVar(value=64)
        self.var_omega_mode = tk.StringVar(value="auto")
        self.var_omega = tk.DoubleVar(value=1.90)
        self.var_eps = tk.StringVar(value="1e-10")
        self.var_nmax = tk.IntVar(value=500000)
        self.var_interp = tk.StringVar(value="x")
        self.var_conv = tk.BooleanVar(value=True)

        self._build()
        self._sync_method()

    def _build(self):
        ttk.Label(self, text="МЕТОД", style="Header.TLabel").pack(anchor=tk.W)
        mf = ttk.Frame(self, style="Panel.TFrame"); mf.pack(fill=tk.X, pady=(2, 8))
        ttk.Radiobutton(mf, text="Метод верхней релаксации (МВР)",
                        variable=self.var_method, value="sor",
                        command=self._sync_method).pack(anchor=tk.W)
        ttk.Radiobutton(mf, text="Метод Зейделя (ω = 1)",
                        variable=self.var_method, value="seidel",
                        command=self._sync_method).pack(anchor=tk.W)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=8)

        ttk.Label(self, text="ЗАДАЧА", style="Header.TLabel").pack(anchor=tk.W)
        pf = ttk.Frame(self, style="Panel.TFrame"); pf.pack(fill=tk.X, pady=(2, 8))
        ttk.Radiobutton(pf, text="Тестовая (точное решение известно)",
                        variable=self.var_problem, value="test").pack(anchor=tk.W)
        ttk.Radiobutton(pf, text="Основная (точность по Рунге)",
                        variable=self.var_problem, value="main").pack(anchor=tk.W)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=8)

        gb = ttk.LabelFrame(self, text="Сетка", style="Card.TLabelframe",
                            padding=10)
        gb.pack(fill=tk.X, pady=4)
        self._entry(gb, "Разбиений по x  (n):", self.var_n)
        self._entry(gb, "Разбиений по y  (m):", self.var_m)
        bf = ttk.Frame(gb, style="Panel.TFrame"); bf.pack(fill=tk.X, pady=(6, 0))
        for val in (16, 32, 64, 128, 256):
            ttk.Button(bf, text=str(val), width=4, style="Grid.TButton",
                       command=lambda v=val: self._set_grid(v)).pack(side=tk.LEFT, padx=1)

        self.omega_box = ttk.LabelFrame(self, text="Параметр ω (для МВР)",
                                        style="Card.TLabelframe", padding=10)
        self.omega_box.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(self.omega_box, text="Оптимальный",
                        variable=self.var_omega_mode, value="auto",
                        command=self._sync_omega).pack(anchor=tk.W)
        ttk.Radiobutton(self.omega_box, text="Задать вручную:",
                        variable=self.var_omega_mode, value="manual",
                        command=self._sync_omega).pack(anchor=tk.W)
        self.omega_scale = ttk.Scale(self.omega_box, from_=1.0, to=1.999,
                                     variable=self.var_omega, orient=tk.HORIZONTAL,
                                     command=self._omega_slide)
        self.omega_scale.pack(fill=tk.X, pady=(4, 2))
        self.omega_lbl = ttk.Label(self.omega_box, text="ω = 1.900",
                                   style="Panel.TLabel")
        self.omega_lbl.pack(anchor=tk.W)

        sb = ttk.LabelFrame(self, text="Критерии остановки",
                            style="Card.TLabelframe", padding=10)
        sb.pack(fill=tk.X, pady=4)
        self._entry(sb, "Точность ε_мет:", self.var_eps, 12)
        self._entry(sb, "Макс. итераций Nmax:", self.var_nmax, 12)

        ib = ttk.LabelFrame(self, text="Начальное приближение",
                            style="Card.TLabelframe", padding=10)
        ib.pack(fill=tk.X, pady=4)
        ttk.Radiobutton(ib, text="Интерполяция по x",
                        variable=self.var_interp, value="x").pack(anchor=tk.W)
        ttk.Radiobutton(ib, text="Интерполяция по y",
                        variable=self.var_interp, value="y").pack(anchor=tk.W)

        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, pady=10)
        self.btn_run = ttk.Button(self, text=" РАССЧИТАТЬ",
                                  style="Run.TButton", command=self.on_run)
        self.btn_run.pack(fill=tk.X)
        ttk.Checkbutton(self, text="Считать таблицу сходимости",
                        variable=self.var_conv).pack(anchor=tk.W, pady=(8, 0))

    def _entry(self, parent, label, var, width=10):
        f = ttk.Frame(parent, style="Panel.TFrame"); f.pack(fill=tk.X, pady=2)
        ttk.Label(f, text=label, style="Panel.TLabel").pack(side=tk.LEFT)
        ttk.Entry(f, textvariable=var, width=width).pack(side=tk.RIGHT)

    def _set_grid(self, v):
        self.var_n.set(v); self.var_m.set(v)

    def _omega_slide(self, _=None):
        self.omega_lbl.config(text=f"ω = {self.var_omega.get():.3f}")

    def _sync_omega(self):
        manual = (self.var_omega_mode.get() == "manual")
        self.omega_scale.config(state=tk.NORMAL if manual else tk.DISABLED)

    def _sync_method(self):
        is_sor = (self.var_method.get() == "sor")
        for child in self.omega_box.winfo_children():
            try:
                child.config(state=tk.NORMAL if is_sor else tk.DISABLED)
            except tk.TclError:
                pass
        if is_sor:
            self._sync_omega()

    def collect(self):
        eps = float(self.var_eps.get())
        n, m = self.var_n.get(), self.var_m.get()
        if not (2 <= n <= 2000 and 2 <= m <= 2000):
            raise ValueError("n и m должны быть в диапазоне 2…2000")
        method = self.var_method.get()
        if method == "sor" and self.var_omega_mode.get() == "manual":
            omega = f"{self.var_omega.get():.6f}"
        else:
            omega = "auto"
        return dict(problem=self.var_problem.get(), method=method,
                    n=n, m=m, omega=omega, eps=eps,
                    nmax=self.var_nmax.get(), interp=self.var_interp.get(),
                    conv=self.var_conv.get())

class ResultView:
    """Вывод результатов: вкладки «Графики» и «Таблицы» плюс окно справки."""
    def __init__(self, root, container):
        self.root = root
        self.container = container
        self.tabs = None

    def clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def placeholder(self):
        self.clear()
        ttk.Label(self.container,
                  text="Задайте параметры слева и нажмите «РАССЧИТАТЬ».",
                  style="Title.TLabel").pack(pady=70)

    def render(self, d, conv_rows):
        self.clear()
        is_test = (d["problem"] == "test")
        method = "МВР" if d["method"] == "sor" else "Зейдель"
        prob = "Тестовая" if is_test else "Основная"

        ttk.Label(self.container,
                  text=f"{prob} задача · {method} · сетка {d['n']}×{d['m']}",
                  style="Title.TLabel").pack(anchor=tk.W, pady=(6, 4), padx=6)

        self.tabs = ttk.Notebook(self.container)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        tab_plot = ttk.Frame(self.tabs)
        tab_table = ttk.Frame(self.tabs)
        self.tabs.add(tab_plot, text="  Графики  ")
        self.tabs.add(tab_table, text="  Таблицы  ")

        self._build_plots(tab_plot, d, is_test, method)
        self._build_tables(tab_table, d, conv_rows, is_test)

        self.show_result_popup(d, is_test, method)

    def _build_plots(self, parent, d, is_test, method):
        x = np.array(d["x"]); y = np.array(d["y"])
        if is_test:
            v = np.array(d["v"]); ue = np.array(d["u_exact"]); v0 = np.array(d["v0"])
            self._specs = [
                ("Точное решение u*(x, y)", x, y, ue, "viridis"),
                ("Начальное приближение v0", x, y, v0, "cividis"),
                ("Численное решение v(N)", x, y, v, "viridis"),
                ("Погрешность u* − v(N)", x, y, ue - v, "coolwarm"),
            ]
        else:
            v = np.array(d["v"]); v0 = np.array(d["v0"])
            xf = np.array(d["fine_x"]); yf = np.array(d["fine_y"])
            vf = np.array(d["fine_v"]); vfc = vf[::2, ::2]
            self._specs = [
                ("Начальное приближение v0", x, y, v0, "cividis"),
                ("Численное v(N) на (n, m)", x, y, v, "viridis"),
                ("Численное v2 на (2n, 2m)", xf, yf, vf, "viridis"),
                ("Погрешность v(N) − v2", x, y, v - vfc, "coolwarm"),
            ]

        bar = ttk.Frame(parent); bar.pack(fill=tk.X, padx=4, pady=(6, 2))
        ttk.Label(bar, text="График:").pack(side=tk.LEFT, padx=(0, 6))
        self._plot_choice = tk.IntVar(value=0)
        for i, (title, *_rest) in enumerate(self._specs):
            ttk.Radiobutton(bar, text=title, variable=self._plot_choice,
                            value=i, command=self._redraw_plot).pack(side=tk.LEFT, padx=4)

        self.fig = Figure(figsize=(7.5, 5.5), dpi=130)
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        class SaveOnlyToolbar(NavigationToolbar2Tk):
            toolitems = [t for t in NavigationToolbar2Tk.toolitems if t[0] in ('Save',)]

        toolbar = SaveOnlyToolbar(self.canvas, parent)
        toolbar.update()

        ttk.Label(parent, foreground=COLORS["muted"],
                  text="Для экспорта картинки нажмите кнопку сохранения (дискета) внизу.").pack(
            anchor=tk.W, padx=6, pady=(0, 4))

        self._redraw_plot()

    def _redraw_plot(self):
        self.ax.clear()

        self.ax.disable_mouse_rotation() 

        title, x, y, Z, cmap = self._specs[self._plot_choice.get()]
        X, Y = np.meshgrid(x, y)
        surf = self.ax.plot_surface(X, Y, Z, cmap=cmap, edgecolor="none", alpha=0.9)
        self.ax.set_title(title, fontsize=11, pad=10)
        self.ax.set_xlabel("x")
        self.ax.set_ylabel("y")
        self.fig.canvas.draw_idle()

    def _build_tables(self, parent, d, conv_rows, is_test):
        canvas = tk.Canvas(parent, highlightthickness=0, background=COLORS["bg"])
        vbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = ttk.Frame(canvas)
        wid = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        canvas.bind("<MouseWheel>",
                    lambda e: canvas.yview_scroll(int(-e.delta / 120), "units"))

        self._metrics(inner, d, is_test)
        self._values(inner, d, is_test)
        if conv_rows is not None:
            self._convergence(inner, conv_rows, is_test)

    def _metrics(self, parent, d, is_test):
        box = ttk.LabelFrame(parent, text="Таблица расчётов (метрики)",
                             style="Card.TLabelframe", padding=8)
        box.pack(fill=tk.X, padx=6, pady=6)
        tv = ttk.Treeview(box, columns=("p", "v"), show="headings", height=16)
        tv.heading("p", text="Величина"); tv.heading("v", text="Значение")
        tv.column("p", width=440, anchor=tk.W); tv.column("v", width=340, anchor=tk.W)
        for p, v in self._metric_rows(d, is_test):
            tv.insert("", "end", values=(p, v))
        vbar = ttk.Scrollbar(box, orient="vertical", command=tv.yview)
        tv.configure(yscrollcommand=vbar.set)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        tv.pack(fill=tk.X, expand=True)

    def _metric_rows(self, d, is_test):
        rows = [
            ("Область", f"x, y ∈ [{d['a']:g}, {d['b']:g}]"),
            ("Шаги сетки", f"h = {d['h']:.6g},  k = {d['k']:.6g}"),
            ("Метод", "МВР" if d["method"] == "sor" else "Зейдель (ω = 1)"),
            ("Параметр ω", f"{d['omega']:.6f}"),
            ("ω оптимальный", f"{d['omega_opt']:.6f}"),
            ("Спектральный радиус Якоби ρ(B)", f"{d['rho_jacobi']:.6f}"),
            ("Критерий ε_мет", f"{d['eps_met']:.2e}"),
            ("Критерий Nmax", f"{d['Nmax']}"),
            ("Выполнено итераций N", f"{d['iters']}"),
            ("Остановка по", "точности" if d["stop"] == "tolerance" else "числу итераций"),
            ("Достигнутая точность метода ε(N)", f"{d['eps_N']:.6e}"),
            ("Невязка ‖R‖∞ (норма max)", f"{d['residual_inf']:.6e}"),
            ("Невязка ‖R‖₂ (евклидова)", f"{d['residual_2']:.6e}"),
            ("λmin(−A)", f"{d['lambda_min']:.6e}"),
            ("Оценка погрешности метода ‖Z(N)‖", f"{d['z_iter_2']:.6e}"),
        ]
        return rows

    def _values(self, parent, d, is_test):
        box = ttk.LabelFrame(parent, text="Таблица значений сеточной функции",
                             style="Card.TLabelframe", padding=8)
        box.pack(fill=tk.X, padx=6, pady=6)
        x = d["x"]; y = d["y"]
        max_show = 11
        stride = max(1, (len(x) - 1) // (max_show - 1))
        xi = list(range(0, len(x), stride))
        yj = list(range(0, len(y), stride))
        if is_test:
            v = d["v"]; ue = d["u_exact"]
            Z = [[ue[j][i] - v[j][i] for i in xi] for j in yj]
            caption = "Разность u*(x, y) − v(N) в узлах (прорежено)."
        else:
            v = d["v"]; fine = d["fine_v"]
            vfc = [row[::2] for row in fine[::2]]
            Z = [[v[j][i] - vfc[j][i] for i in xi] for j in yj]
            caption = "Разность v(N) − v2(N2) в общих узлах (прорежено)."
        cols = ["y"] + [f"c{i}" for i in xi]
        tv = ttk.Treeview(box, columns=cols, show="headings",
                          height=min(len(yj) + 1, 12))
        tv.heading("y", text="y \\ x"); tv.column("y", width=80, anchor=tk.CENTER)
        for i in xi:
            tv.heading(f"c{i}", text=f"{x[i]:.3f}")
            tv.column(f"c{i}", width=80, anchor=tk.CENTER)
        for jj, j in enumerate(yj):
            vals = [f"{y[j]:.3f}"] + [f"{Z[jj][k]:.2e}" for k in range(len(xi))]
            tv.insert("", "end", values=vals)
        hbar = ttk.Scrollbar(box, orient="horizontal", command=tv.xview)
        tv.configure(xscrollcommand=hbar.set)
        tv.pack(fill=tk.X); hbar.pack(fill=tk.X)
        ttk.Label(box, text=caption, foreground=COLORS["muted"]).pack(
            anchor=tk.W, pady=(4, 0))

    def _convergence(self, parent, rows, is_test):
        title = ("Проверка порядка сходимости (ε1, тестовая)"
                 if is_test else "Проверка порядка сходимости (ε2, основная)")
        box = ttk.LabelFrame(parent, text=title, style="Card.TLabelframe", padding=8)
        box.pack(fill=tk.X, padx=6, pady=6)
        cols = ("n", "omega", "eps", "ratio", "order", "iters", "stop")
        tv = ttk.Treeview(box, columns=cols, show="headings", height=len(rows) + 1)
        heads = [("n", "n×m", 90), ("omega", "ω", 95),
                 ("eps", "ε1" if is_test else "ε2", 150),
                 ("ratio", "отношение", 110), ("order", "порядок", 95),
                 ("iters", "итераций", 95), ("stop", "остановка", 120)]
        for c, t, w in heads:
            tv.heading(c, text=t); tv.column(c, width=w, anchor=tk.CENTER)
        for r in rows:
            ratio = f"{r['ratio']:.3f}" if r["ratio"] else "—"
            order = f"{r['order']:.3f}" if r["order"] else "—"
            stop = "точность" if r["stop"] == "tolerance" else "Nmax"
            tv.insert("", "end", values=(f"{r['n']}×{r['m']}", f"{r['omega']:.5f}",
                                         f"{r['eps']:.4e}", ratio, order,
                                         r["iters"], stop))
        tv.pack(fill=tk.X)
        orders = [r["order"] for r in rows if r["order"] is not None]
        if orders:
            mean = sum(orders[-3:]) / len(orders[-3:])
            note = (f"Наблюдаемый порядок ≈ {mean:.3f}. "
                    + ("Подтверждает 2-й порядок схемы (гладкое решение)."
                       if mean > 1.7 else
                       "Снижен из-за негладкости f = |sin³(πxy)| (теория требует гладкости)."))
            ttk.Label(box, text=note, foreground=COLORS["accent"],
                      wraplength=860).pack(anchor=tk.W, pady=(6, 0))

    def show_result_popup(self, d, is_test, method):
        if is_test:
            text = (
                "Справка для тестовой задачи\n\n"
                f"Сетка: n = {d['n']}, m = {d['m']}\n"
                f"Метод: {method}\n"
                f"Параметр ω: {d['omega']:.6f} (оптимальный {d['omega_opt']:.6f})\n"
                f"Критерии: ε_мет = {d['eps_met']:.1e}, Nmax = {d['Nmax']}\n\n"
                f"Затрачено итераций N: {d['iters']}\n"
                f"Остановка по: {'точности' if d['stop']=='tolerance' else 'числу итераций'}\n"
                f"Достигнутая точность метода: {d['eps_N']:.4e}\n"
                f"Невязка ‖R‖∞: {d['residual_inf']:.4e}\n"
                f"Невязка ‖R‖₂: {d['residual_2']:.4e}\n\n"
                f"Погрешность ε1 = max|u* − v|: {d['eps1']:.4e}\n"
                f"Узел макс. отклонения: x = {d['eps1_x']:g}, y = {d['eps1_y']:g}\n"
                f"Оценка погрешности схемы: {d['scheme_bound']:.4e}\n\n"
                f"Требуемая точность ε ≤ {EPS_TARGET:.1e}")
            messagebox.showinfo("Результаты (тестовая задача)", text)
        else:
            text = (
                "Справка для основной задачи\n\n"
                f"Сетка: n = {d['n']}, m = {d['m']}\n"
                f"Метод: {method}\n"
                f"Параметр ω: {d['omega']:.6f} (оптимальный {d['omega_opt']:.6f})\n"
                f"Критерии: ε_мет = {d['eps_met']:.1e}, Nmax = {d['Nmax']}\n\n"
                f"Затрачено итераций N: {d['iters']}\n"
                f"Остановка по: {'точности' if d['stop']=='tolerance' else 'числу итераций'}\n"
                f"Достигнутая точность метода: {d['eps_N']:.4e}\n"
                f"Невязка ‖R‖∞: {d['residual_inf']:.4e}\n\n"
                "Контроль точности (правило Рунге)\n"
                f"Сетка с половинным шагом: n = {d['fine_n']}, m = {d['fine_m']}\n"
                f"Итераций на (2n, 2m): {d['fine_iters']}\n"
                f"Точность ε2 = max|v − v2|: {d['eps2']:.4e}\n"
                f"Узел макс. отклонения: x = {d['eps2_x']:g}, y = {d['eps2_y']:g}\n\n"
                f"Требуемая точность ε ≤ {EPS_TARGET:.1e}")
            messagebox.showinfo("Результаты (основная задача)", text)
