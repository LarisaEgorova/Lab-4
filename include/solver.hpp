// ============================================================================
//  solver.hpp — вычислительное ядро.
//  Зейдель/МВР для 5-точечной схемы (matrix-free), нормы невязки,
//  omega_opt (7.14), lambda_min(-A), rho(B), погрешности eps1/eps2,
//  оценка погрешности схемы (теорема 7.7).
// ============================================================================
#ifndef POISSON_SOLVER_HPP
#define POISSON_SOLVER_HPP

#include "grid.hpp"
#include <functional>
#include <string>

namespace solver {

using Fn2 = std::function<double(double, double)>;
using Fn1 = std::function<double(double)>;

enum class Method { SEIDEL, SOR };
enum class InterpDir { X, Y };

void set_boundary(Field& v, const Grid& g,
                  Fn1 mu1, Fn1 mu2, Fn1 mu3, Fn1 mu4);

void initial_interpolation(Field& v, const Grid& g,
                           Fn1 mu1, Fn1 mu2, Fn1 mu3, Fn1 mu4,
                           InterpDir dir);

void build_rhs(Field& f, const Grid& g, Fn2 frhs);

struct IterStats {
    int    iters = 0;
    double eps_N = 0.0;       // ‖v^N − v^(N−1)‖_∞ — норма шага
    double rho_est = 0.0;     // наблюдаемый спектральный радиус (running-max отношения шагов)
    double eps_apost = 0.0;   // апостериорная оценка погрешности: ρ·ε_N/(1−ρ)
    std::string stop;
};

IterStats iterate(Field& v, const Field& f, const Grid& g,
                  Method method, double omega,
                  double eps_met, int Nmax);

void residual_norms(const Field& v, const Field& f, const Grid& g,
                    double& r_inf, double& r_2);

double rho_jacobi(const Grid& g);
double omega_opt(const Grid& g);
double lambda_min(const Grid& g);

double eps1_error(const Field& v, const Grid& g, Fn2 u_exact,
                  int& imax, int& jmax);

double eps2_runge(const Field& v_coarse, const Field& v_fine,
                  const Grid& g_coarse, int& imax, int& jmax);

struct SchemeBound {
    double M1, M2;
    double bound;
};
SchemeBound scheme_bound(const Grid& g, Fn2 d4x, Fn2 d4y);

} // namespace solver

#endif // POISSON_SOLVER_HPP
