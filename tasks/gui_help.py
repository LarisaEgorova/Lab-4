"""Всплывающее окно справки с описанием лабораторной работы (вариант 2)."""
import tkinter as tk
from tkinter import ttk

from gui_widgets import COLORS

LAB_TITLE = "Лабораторная работа №4\nЗадача Дирихле для уравнения Пуассона"

LAB_TEXT = """\
ЦЕЛЬ РАБОТЫ
Решение разностных схем итерационным методом, решение систем линейных
уравнений большой размерности. Проверка сходимости, анализ структуры
погрешности и её компонент, ускорение сходимости. Решение модельной
задачи с заданной погрешностью и точностью.

ПОСТАНОВКА
Основная задача (задача Дирихле для уравнения Пуассона):
    Δu(x, y) = −f(x, y),   x ∈ (a, b),  y ∈ (c, d);
    u(a, y) = μ1(y),  u(b, y) = μ2(y);
    u(x, c) = μ3(x),  u(x, d) = μ4(x).
Тестовая задача: берётся известная функция u*(x, y), а правая часть f*
и граничные условия подбираются так, чтобы u* была точным решением.
Это позволяет напрямую измерить погрешность.

ВАРИАНТ 2
    Область:    a; b; c; d = −1; 1; −1; 1
    Тестовая:   u*(x, y) = exp(1 − x² − y²)
                f*(x, y) = 4(1 − x² − y²)·exp(1 − x² − y²)
                μ*1 = μ*2 = exp(−y²),  μ*3 = μ*4 = exp(−x²)
    Основная:   f(x, y) = |sin³(πxy)|
                μ1 = μ2 = 1 − y²,  μ3 = μ4 = |sin(πx)|
    Требуемая точность: ε = 0.5·10⁻⁶

ДИСКРЕТИЗАЦИЯ
Разностная схема второго порядка на прямоугольной сетке (n, m):
    h = (b − a) / n,  k = (d − c) / m.
Система решается методом верхней релаксации (МВР). Начальное приближение —
линейная интерполяция граничных условий по направлению x или y. Остановка
задаётся критериями: по точности ε_мет и по числу итераций Nmax.
Параметр метода ω ∈ (0, 2) берётся близким к оптимальному.

ПОГРЕШНОСТЬ И ТОЧНОСТЬ
Тестовая задача: ε1 = max|u* − v(N)| — максимум разности точного и
численного решений в узлах сетки.
Основная задача: точное решение неизвестно, поэтому точность ε2
оценивается по правилу Рунге — сравнением решений на сетках (n, m)
и (2n, 2m) в общих узлах.

ПОРЯДОК СХОДИМОСТИ
Порядок — свойство схемы. Для схемы второго порядка при гладком решении
погрешность ведёт себя как C·h²: при удвоении сетки она падает примерно
в 4 раза (порядок 2).
    Тестовая задача (u* гладкая) — порядок около 2.
    Основная задача (f с модулем синуса) — порядок около 1, так как
    решение недостаточно гладкое.

МЕТОД ВЕРХНЕЙ РЕЛАКСАЦИИ
Обновление узла:
    v ← (1 − ω)·v + ω·[ f + (v_лев + v_прав)/h²
                          + (v_низ + v_верх)/k² ] / (2/h² + 2/k²).
При ω = 1 это метод Зейделя. Оптимальное ω находится по формуле
    ω = 2 / (1 + √(1 − ρ²)),
где ρ — спектральный радиус матрицы Якоби. При оптимальном ω метод
верхней релаксации сходится в десятки раз быстрее метода Зейделя.
"""

def show_help_window(parent):
    win = tk.Toplevel(parent)
    win.title("Справка по лабораторной работе")
    win.geometry("620x560")
    win.minsize(520, 420)
    win.transient(parent)
    win.configure(background=COLORS["card"])

    tk.Label(win, text=LAB_TITLE, font=("Segoe UI", 12, "bold"),
             bg=COLORS["card"], fg=COLORS["heading"], justify="left").pack(
        fill=tk.X, padx=16, pady=(14, 8))

    frame = tk.Frame(win, background=COLORS["card"])
    frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))
    scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL)
    text = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scroll.set,
                   font=("Consolas", 10), relief=tk.FLAT,
                   background="#fbfdff", fg=COLORS["text"], padx=12, pady=10)
    scroll.config(command=text.yview)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    text.insert("1.0", LAB_TEXT)
    text.config(state=tk.DISABLED)

    ttk.Button(win, text="Закрыть", command=win.destroy).pack(pady=(0, 12))

    win.update_idletasks()
    px = parent.winfo_rootx() + parent.winfo_width() // 2 - win.winfo_width() // 2
    py = parent.winfo_rooty() + parent.winfo_height() // 2 - win.winfo_height() // 2
    win.geometry(f"+{max(px,0)}+{max(py,0)}")
    win.grab_set()
    return win
