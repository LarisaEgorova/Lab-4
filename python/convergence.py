"""Проверка порядка сходимости.

Для серии сеток вычисляются погрешность (ε1 для тестовой задачи или ε2 по
правилу Рунге для основной), отношение соседних погрешностей и оценка
порядка как log2 отношения. Для схемы второго порядка при гладком решении
отношение стремится к 4, а порядок — к 2.
"""
import math

import core_runner as cr

TEST_GRIDS_SOR    = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
MAIN_GRIDS_SOR    = [(8, 8), (16, 16), (32, 32), (64, 64), (128, 128)]
TEST_GRIDS_SEIDEL = [(8, 8), (16, 16), (32, 32), (64, 64)]
MAIN_GRIDS_SEIDEL = [(8, 8), (16, 16), (32, 32), (64, 64)]

EPS_MET = 1e-11
NMAX = 1_000_000

def convergence_test(method="sor", grids=None):
    if grids is None:
        grids = TEST_GRIDS_SEIDEL if method == "seidel" else TEST_GRIDS_SOR
    rows = []
    for (n, m) in grids:
        d = cr.run_solver("test", method, n, m,
                          omega="auto", eps=EPS_MET, nmax=NMAX, grids=False)
        rows.append(dict(n=n, m=m, omega=d["omega"], eps_met=EPS_MET,
                         eps=d["eps1"], iters=d["iters"], stop=d["stop"]))
    _fill_ratio(rows)
    return rows

def convergence_main(method="sor", grids=None):
    if grids is None:
        grids = MAIN_GRIDS_SEIDEL if method == "seidel" else MAIN_GRIDS_SOR
    rows = []
    for (n, m) in grids:
        d = cr.run_solver("main", method, n, m,
                          omega="auto", eps=EPS_MET, nmax=NMAX, grids=False)
        rows.append(dict(n=n, m=m, omega=d["omega"], eps_met=EPS_MET,
                         eps=d["eps2"], iters=d["iters"], stop=d["stop"]))
    _fill_ratio(rows)
    return rows

def _fill_ratio(rows):
    """Заполнить отношение соседних погрешностей и оценку порядка."""
    for i, r in enumerate(rows):
        if i == 0:
            r["ratio"] = None
            r["order"] = None
        else:
            ratio = rows[i - 1]["eps"] / r["eps"] if r["eps"] > 0 else 0.0
            r["ratio"] = ratio
            r["order"] = math.log2(ratio) if ratio > 0 else float("nan")
