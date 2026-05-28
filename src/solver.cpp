// ============================================================================
//  solver.cpp — реализация вычислительного ядра.
// ============================================================================
#include "solver.hpp"
#include <cmath>
#include <algorithm>
#include <iostream>

namespace solver {

static const double PI = 3.14159265358979323846;

void set_boundary(Field& v, const Grid& g,
                  Fn1 mu1, Fn1 mu2, Fn1 mu3, Fn1 mu4) {
    const int n = g.n, m = g.m;
    for (int j = 0; j <= m; ++j) {
        v(0, j) = mu1(g.y(j));
        v(n, j) = mu2(g.y(j));
    }
    for (int i = 0; i <= n; ++i) {
        v(i, 0) = mu3(g.x(i));
        v(i, m) = mu4(g.x(i));
    }
}

void initial_interpolation(Field& v, const Grid& g,
                           Fn1 mu1, Fn1 mu2, Fn1 mu3, Fn1 mu4,
                           InterpDir dir) {
    const int n = g.n, m = g.m;
    set_boundary(v, g, mu1, mu2, mu3, mu4);
    for (int i = 1; i < n; ++i) {
        for (int j = 1; j < m; ++j) {
            if (dir == InterpDir::X) {
                double left  = mu1(g.y(j));
                double right = mu2(g.y(j));
                double t = (g.x(i) - g.a) / (g.b - g.a);
                v(i, j) = left + (right - left) * t;
            } else {
                double bottom = mu3(g.x(i));
                double top    = mu4(g.x(i));
                double t = (g.y(j) - g.c) / (g.d - g.c);
                v(i, j) = bottom + (top - bottom) * t;
            }
        }
    }
}

void build_rhs(Field& f, const Grid& g, Fn2 frhs) {
    const int n = g.n, m = g.m;
    for (int i = 1; i < n; ++i)
        for (int j = 1; j < m; ++j)
            f(i, j) = frhs(g.x(i), g.y(j));
}

// (-A)v = F:  a2*v_ij - cx*(v_{i-1,j}+v_{i+1,j}) - cy*(v_{i,j-1}+v_{i,j+1}) = f_ij
// МВР:  v_ij = (1-w)*v_ij + w*( f_ij + cx*(...) + cy*(...) ) / a2,  Зейдель = w=1.
IterStats iterate(Field& v, const Field& f, const Grid& g,
                  Method method, double omega,
                  double eps_met, int Nmax) {
    const int n = g.n, m = g.m;
    const double cx = 1.0 / (g.h * g.h);
    const double cy = 1.0 / (g.k * g.k);
    const double a2 = 2.0 * (cx + cy);
    const double w  = (method == Method::SEIDEL) ? 1.0 : omega;

    IterStats st;
    st.stop = "maxiter";

    for (int s = 1; s <= Nmax; ++s) {
        double eps_max = 0.0;
        for (int j = 1; j < m; ++j) {
            for (int i = 1; i < n; ++i) {
                double v_old = v(i, j);
                double gs = (f(i, j)
                             + cx * (v(i - 1, j) + v(i + 1, j))
                             + cy * (v(i, j - 1) + v(i, j + 1))) / a2;
                double v_new = (1.0 - w) * v_old + w * gs;
                v(i, j) = v_new;
                double diff = std::fabs(v_new - v_old);
                if (diff > eps_max) eps_max = diff;
            }
        }
        // прогресс в Python (stderr); отмена из GUI = kill процесса
        if (s % 2000 == 0) std::cerr << "ITER:" << s << ":" << eps_max << "\n";

        st.iters = s;
        st.eps_N = eps_max;
        if (eps_max < eps_met) { st.stop = "tolerance"; break; }
    }
    return st;
}

void residual_norms(const Field& v, const Field& f, const Grid& g,
                    double& r_inf, double& r_2) {
    const int n = g.n, m = g.m;
    const double cx = 1.0 / (g.h * g.h);
    const double cy = 1.0 / (g.k * g.k);
    const double a2 = 2.0 * (cx + cy);
    r_inf = 0.0;
    double sum2 = 0.0;
    for (int i = 1; i < n; ++i) {
        for (int j = 1; j < m; ++j) {
            double r = a2 * v(i, j)
                     - cx * (v(i - 1, j) + v(i + 1, j))
                     - cy * (v(i, j - 1) + v(i, j + 1))
                     - f(i, j);
            double ar = std::fabs(r);
            if (ar > r_inf) r_inf = ar;
            sum2 += r * r;
        }
    }
    r_2 = std::sqrt(sum2);
}

double rho_jacobi(const Grid& g) {
    const double cx = 1.0 / (g.h * g.h);
    const double cy = 1.0 / (g.k * g.k);
    return (cx * std::cos(PI / g.n) + cy * std::cos(PI / g.m)) / (cx + cy);
}

double omega_opt(const Grid& g) {
    double rho = rho_jacobi(g);
    return 2.0 / (1.0 + std::sqrt(1.0 - rho * rho));
}

double lambda_min(const Grid& g) {
    const double cx = 1.0 / (g.h * g.h);
    const double cy = 1.0 / (g.k * g.k);
    double sx = std::sin(PI / (2.0 * g.n));
    double sy = std::sin(PI / (2.0 * g.m));
    return 4.0 * cx * sx * sx + 4.0 * cy * sy * sy;
}

double eps1_error(const Field& v, const Grid& g, Fn2 u_exact,
                  int& imax, int& jmax) {
    const int n = g.n, m = g.m;
    double eps1 = 0.0;
    imax = jmax = 0;
    for (int i = 0; i <= n; ++i) {
        for (int j = 0; j <= m; ++j) {
            double diff = std::fabs(u_exact(g.x(i), g.y(j)) - v(i, j));
            if (diff > eps1) { eps1 = diff; imax = i; jmax = j; }
        }
    }
    return eps1;
}

double eps2_runge(const Field& v_coarse, const Field& v_fine,
                  const Grid& g_coarse, int& imax, int& jmax) {
    const int n = g_coarse.n, m = g_coarse.m;
    double eps2 = 0.0;
    imax = jmax = 0;
    for (int i = 0; i <= n; ++i) {
        for (int j = 0; j <= m; ++j) {
            double diff = std::fabs(v_coarse(i, j) - v_fine(2 * i, 2 * j));
            if (diff > eps2) { eps2 = diff; imax = i; jmax = j; }
        }
    }
    return eps2;
}

SchemeBound scheme_bound(const Grid& g, Fn2 d4x, Fn2 d4y) {
    const int S = 400;
    double M1 = 0.0, M2 = 0.0;
    for (int i = 0; i <= S; ++i) {
        for (int j = 0; j <= S; ++j) {
            double x = g.a + (g.b - g.a) * i / S;
            double y = g.c + (g.d - g.c) * j / S;
            M1 = std::max(M1, std::fabs(d4x(x, y)));
            M2 = std::max(M2, std::fabs(d4y(x, y)));
        }
    }
    double L2 = (g.b - g.a) * (g.b - g.a) + (g.d - g.c) * (g.d - g.c);
    double bound = (M1 * g.h * g.h + M2 * g.k * g.k) / 16.0 * L2;
    return SchemeBound{M1, M2, bound};
}

} // namespace solver
