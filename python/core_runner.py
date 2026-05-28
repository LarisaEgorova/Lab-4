"""Компиляция и запуск вычислительного ядра на C++.

Ядро вызывается как отдельный процесс, результат возвращается через JSON.
Компилятор C++ ищется автоматически среди g++, clang++ и cl.exe (MSVC),
а также в типовых путях установки на Windows.
"""
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
INCLUDE_DIR = os.path.join(ROOT, "include")
SRC_DIR = os.path.join(ROOT, "src")
BUILD_DIR = os.path.join(ROOT, "build")
OUT_DIR = os.path.join(ROOT, "output")

IS_WIN = (os.name == "nt")
EXE = os.path.join(BUILD_DIR, "solver" + (".exe" if IS_WIN else ""))

SOURCES = ["main.cpp", "problem.cpp", "solver.cpp"]
HEADERS = ["problem.hpp", "grid.hpp", "solver.hpp", "json_writer.hpp"]

WINDOWS_GXX_CANDIDATES = [
    r"C:\w64devkit\bin\g++.exe",
    r"C:\msys64\mingw64\bin\g++.exe",
    r"C:\msys64\ucrt64\bin\g++.exe",
    r"C:\MinGW\bin\g++.exe",
    r"C:\mingw64\bin\g++.exe",
    r"C:\TDM-GCC-64\bin\g++.exe",
    r"C:\Program Files\LLVM\bin\clang++.exe",
    r"C:\Program Files (x86)\LLVM\bin\clang++.exe"
]

_ACTIVE_PROCESS = None
_IS_CANCELLED = False

def _find_compiler():
    """Найти компилятор. Возвращает (вид, путь) или (None, None)."""
    for name in ("g++", "clang++"):
        path = shutil.which(name)
        if path:
            return ("gcc", path)

    if IS_WIN:
        for cand in WINDOWS_GXX_CANDIDATES:
            if os.path.exists(cand):
                return ("gcc", cand)

    cl = shutil.which("cl")
    if cl:
        return ("msvc", cl)

    return (None, None)

def _build_cmd(kind, comp, sources):
    if kind == "gcc":
        return [comp, "-O2", "-std=c++17", "-I", INCLUDE_DIR, "-o", EXE] + sources
    if kind == "msvc":
        return [comp, "/nologo", "/O2", "/EHsc", "/std:c++17",
                f"/I{INCLUDE_DIR}", *sources,
                f"/Fe:{EXE}", f"/Fo:{BUILD_DIR}\\"]
    raise RuntimeError("Неизвестный компилятор")

def compile_core(force=False):
    """Собрать ядро, если бинарник отсутствует или исходники изменились."""
    os.makedirs(BUILD_DIR, exist_ok=True)
    sources = [os.path.join(SRC_DIR, s) for s in SOURCES]
    headers = [os.path.join(INCLUDE_DIR, h) for h in HEADERS]

    need = force or not os.path.exists(EXE)
    if not need:
        exe_t = os.path.getmtime(EXE)
        for f in sources + headers:
            if os.path.exists(f) and os.path.getmtime(f) > exe_t:
                need = True
                break
    if not need:
        return EXE

    kind, comp = _find_compiler()
    if comp is None:
        raise RuntimeError(
            "Не найден компилятор C++ (g++, clang++ или cl.exe). \n"
            "Установите MinGW-w64 / w64devkit и добавьте его в PATH, \n"
            "либо распакуйте на диск C:\\ и скрипт найдет его сам."
        )

    cmd = _build_cmd(kind, comp, sources)
    print(f"[compile] Компилятор найден: {comp}")

    custom_env = os.environ.copy()
    comp_dir = os.path.dirname(comp)
    custom_env["PATH"] = comp_dir + os.pathsep + custom_env.get("PATH", "")

    res = subprocess.run(cmd, capture_output=True, text=True, env=custom_env)

    if res.returncode != 0:
        raise RuntimeError("Ошибка компиляции ядра:\n" + res.stdout + res.stderr)

    print("[compile] Успешно скомпилировано ->", EXE)
    return EXE

def cancel_active_process():
    """Прервать текущий расчет (вызывается из GUI)."""
    global _ACTIVE_PROCESS, _IS_CANCELLED
    _IS_CANCELLED = True
    if _ACTIVE_PROCESS and _ACTIVE_PROCESS.poll() is None:
        _ACTIVE_PROCESS.kill()

def run_solver(problem, method, n, m,
               omega="auto", eps=1e-10, nmax=500000,
               interp="x", grids=True, stride=1, out_name=None, progress_cb=None):
    """Запустить ядро с заданными параметрами и вернуть результат как dict."""
    global _ACTIVE_PROCESS, _IS_CANCELLED
    _IS_CANCELLED = False

    compile_core()
    os.makedirs(OUT_DIR, exist_ok=True)
    if out_name is None:
        out_name = f"{problem}_{method}_{n}x{m}.json"
    out_path = os.path.join(OUT_DIR, out_name)

    cmd = [EXE,
           "--problem", problem, "--method", method,
           "--n", str(n), "--m", str(m),
           "--omega", str(omega), "--eps", repr(eps),
           "--nmax", str(nmax), "--interp", interp,
           "--grids", "on" if grids else "off",
           "--stride", str(stride), "--out", out_path]

    custom_env = os.environ.copy()
    kind, comp = _find_compiler()
    if comp:
        comp_dir = os.path.dirname(comp)
        custom_env["PATH"] = comp_dir + os.pathsep + custom_env.get("PATH", "")

    _ACTIVE_PROCESS = subprocess.Popen(
        cmd, env=custom_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if IS_WIN else 0
    )

    err_output = []
    # stderr ядра: строки "ITER:s:eps" — прогресс; отмена из GUI убивает процесс
    for line in _ACTIVE_PROCESS.stderr:
        line = line.strip()
        if line.startswith("ITER:"):
            parts = line.split(":")
            if len(parts) >= 3 and progress_cb:
                progress_cb(int(parts[1]), float(parts[2]))
        elif line:
            err_output.append(line)

    _ACTIVE_PROCESS.wait()

    if _IS_CANCELLED:
        raise InterruptedError("Расчёт был прерван пользователем.")

    if _ACTIVE_PROCESS.returncode != 0:
        raise RuntimeError("Ошибка запуска ядра:\n" + "\n".join(err_output))

    with open(out_path, "r", encoding="utf-8") as fh:
        return json.load(fh)

if __name__ == "__main__":
    compile_core(force=True)