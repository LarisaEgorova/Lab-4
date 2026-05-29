// ============================================================================
//  main.cpp — CLI вычислительного ядра.
//  Параметры: --problem test|main, --method seidel|sor, --n, --m,
//  --omega auto|<число>, --eps, --nmax, --interp x|y, --grids on|off,
//  --stride, --out. Для основной задачи сетка (2n,2m) считается автоматически.
// ============================================================================
#include "problem.hpp"
#include "grid.hpp"
#include "solver.hpp"
#include "json_writer.hpp"

#include <iostream>
#include <fstream>
#include <map>
#include <string>
#include <vector>
#include <cstdlib>

using namespace solver;

static std::map<std::string, std::string> parse_args(int argc, char** argv) {
    std::map<std::string, std::string> a;
    for (int i = 1; i + 1 < argc; i += 2) {
        std::string key = argv[i];
        if (key.rfind("--", 0) == 0) a[key.substr(2)] = argv[i + 1];
    }
    return a;
}
static std::string get(std::map<std::string,std::string>& a, const std::string& k, const std::string& def) {
    auto it = a.find(k); return it == a.end() ? def : it->second;
}

static std::vector<double> axis(const Grid& g, char ax, int stride) {
    std::vector<double> v;
    if (ax == 'x') for (int i = 0; i <= g.n; i += stride) v.push_back(g.x(i));
    else           for (int j = 0; j <= g.m; j += stride) v.push_back(g.y(j));
    return v;
}

struct SolveOut {
    Field v, v0;
    IterStats st;
    double r_inf, r_2, lam_min, omega_used, omega_o, rho;
    SolveOut(int n, int m) : v(n, m), v0(n, m) {}
};

static SolveOut solve_one(const Grid& g, bool is_test, Method method,
                          double omega_req, bool omega_auto,
                          double eps_met, int Nmax, InterpDir dir) {
    SolveOut out(g.n, g.m);

    Fn2 frhs = is_test ? Fn2(problem::f_test) : Fn2(problem::f_main);
    Fn1 mu1  = is_test ? Fn1(problem::mu1_test) : Fn1(problem::mu1_main);
    Fn1 mu2  = is_test ? Fn1(problem::mu2_test) : Fn1(problem::mu2_main);
    Fn1 mu3  = is_test ? Fn1(problem::mu3_test) : Fn1(problem::mu3_main);
    Fn1 mu4  = is_test ? Fn1(problem::mu4_test) : Fn1(problem::mu4_main);

    out.rho      = rho_jacobi(g);
    out.omega_o  = omega_opt(g);
    out.omega_used = (method == Method::SEIDEL) ? 1.0
                    : (omega_auto ? out.omega_o : omega_req);

    initial_interpolation(out.v, g, mu1, mu2, mu3, mu4, dir);
    out.v0 = out.v;

    Field f(g.n, g.m);
    build_rhs(f, g, frhs);

    out.st = iterate(out.v, f, g, method, out.omega_used, eps_met, Nmax);

    residual_norms(out.v, f, g, out.r_inf, out.r_2);
    out.lam_min = lambda_min(g);
    return out;
}

int main(int argc, char** argv) {
    auto a = parse_args(argc, argv);

    std::string problem_s = get(a, "problem", "test");
    std::string method_s  = get(a, "method",  "sor");
    int    n      = std::atoi(get(a, "n", "64").c_str());
    int    m      = std::atoi(get(a, "m", "64").c_str());
    std::string omega_s = get(a, "omega", "auto");
    double eps_met= std::atof(get(a, "eps", "1e-9").c_str());
    int    Nmax   = std::atoi(get(a, "nmax", "500000").c_str());
    std::string interp_s = get(a, "interp", "x");
    bool   grids  = (get(a, "grids", "on") == "on");
    int    stride = std::atoi(get(a, "stride", "1").c_str());
    std::string outpath  = get(a, "out", "result.json");

    bool   is_test = (problem_s == "test");
    Method method  = (method_s == "seidel") ? Method::SEIDEL : Method::SOR;
    InterpDir dir  = (interp_s == "y") ? InterpDir::Y : InterpDir::X;
    bool   omega_auto = (omega_s == "auto");
    double omega_req  = omega_auto ? 0.0 : std::atof(omega_s.c_str());

    std::ofstream os(outpath);
    if (!os) { std::cerr << "Cannot open output: " << outpath << "\n"; return 1; }

    Grid g(n, m, problem::A, problem::B, problem::C, problem::D);

    if (is_test) {
        SolveOut s = solve_one(g, true, method, omega_req, omega_auto,
                               eps_met, Nmax, dir);

        int imax, jmax;
        double eps1 = eps1_error(s.v, g, Fn2(problem::u_exact), imax, jmax);
        SchemeBound sb = scheme_bound(g, Fn2(problem::u_d4x), Fn2(problem::u_d4y));

        double z_iter_2 = s.r_2 / s.lam_min;
        double total    = sb.bound + z_iter_2;

        Json J(os);
        J.kv("problem", std::string("test"));
        J.kv("method", method_s);
        J.kv("variant", problem::VARIANT);
        J.kv("a", problem::A); J.kv("b", problem::B);
        J.kv("c", problem::C); J.kv("d", problem::D);
        J.kv("n", n); J.kv("m", m); J.kv("h", g.h); J.kv("k", g.k);
        J.kv("omega", s.omega_used);
        J.kv("omega_opt", s.omega_o);
        J.kv("rho_jacobi", s.rho);
        J.kv("eps_met", eps_met);
        J.kv("Nmax", Nmax);
        J.kv("interp", interp_s);
        J.kv("iters", s.st.iters);
        J.kv("stop", s.st.stop);
        J.kv("eps_N", s.st.eps_N);
        J.kv("rho_est", s.st.rho_est);
        J.kv("eps_apost", s.st.eps_apost);
        J.kv("residual_inf", s.r_inf);
        J.kv("residual_2", s.r_2);
        J.kv("lambda_min", s.lam_min);
        J.kv("z_iter_2", z_iter_2);
        J.kv("scheme_M1", sb.M1);
        J.kv("scheme_M2", sb.M2);
        J.kv("scheme_bound", sb.bound);
        J.kv("total_bound", total);
        J.kv("eps1", eps1);
        J.kv("eps1_i", imax); J.kv("eps1_j", jmax);
        J.kv("eps1_x", g.x(imax)); J.kv("eps1_y", g.y(jmax));
        if (grids) {
            Field ue(g.n, g.m);
            for (int i = 0; i <= g.n; ++i)
                for (int j = 0; j <= g.m; ++j)
                    ue(i, j) = problem::u_exact(g.x(i), g.y(j));
            J.array("x", axis(g, 'x', stride));
            J.array("y", axis(g, 'y', stride));
            J.grid2d("v", s.v, g, stride);
            J.grid2d("u_exact", ue, g, stride);
            J.grid2d("v0", s.v0, g, stride);
        }
    } else {
        SolveOut sc = solve_one(g, false, method, omega_req, omega_auto,
                                eps_met, Nmax, dir);
        Grid gf(2 * n, 2 * m, problem::A, problem::B, problem::C, problem::D);
        SolveOut sf = solve_one(gf, false, method, 0.0, /*omega_auto=*/true,
                                eps_met, Nmax, dir);

        int imax, jmax;
        double eps2 = eps2_runge(sc.v, sf.v, g, imax, jmax);

        double z_iter_2  = sc.r_2 / sc.lam_min;
        double z_iter_2f = sf.r_2 / sf.lam_min;

        Json J(os);
        J.kv("problem", std::string("main"));
        J.kv("method", method_s);
        J.kv("variant", problem::VARIANT);
        J.kv("a", problem::A); J.kv("b", problem::B);
        J.kv("c", problem::C); J.kv("d", problem::D);
        J.kv("eps_met", eps_met);
        J.kv("Nmax", Nmax);
        J.kv("interp", interp_s);
        J.kv("n", n); J.kv("m", m); J.kv("h", g.h); J.kv("k", g.k);
        J.kv("omega", sc.omega_used); J.kv("omega_opt", sc.omega_o);
        J.kv("rho_jacobi", sc.rho);
        J.kv("iters", sc.st.iters); J.kv("stop", sc.st.stop);
        J.kv("eps_N", sc.st.eps_N);
        J.kv("rho_est", sc.st.rho_est);
        J.kv("eps_apost", sc.st.eps_apost);
        J.kv("residual_inf", sc.r_inf); J.kv("residual_2", sc.r_2);
        J.kv("lambda_min", sc.lam_min); J.kv("z_iter_2", z_iter_2);
        J.kv("fine_n", gf.n); J.kv("fine_m", gf.m);
        J.kv("fine_h", gf.h); J.kv("fine_k", gf.k);
        J.kv("omega2", sf.omega_used); J.kv("omega2_opt", sf.omega_o);
        J.kv("fine_iters", sf.st.iters); J.kv("fine_stop", sf.st.stop);
        J.kv("fine_eps_N", sf.st.eps_N);
        J.kv("fine_rho_est", sf.st.rho_est);
        J.kv("fine_eps_apost", sf.st.eps_apost);
        J.kv("fine_residual_inf", sf.r_inf); J.kv("fine_residual_2", sf.r_2);
        J.kv("fine_lambda_min", sf.lam_min); J.kv("fine_z_iter_2", z_iter_2f);
        J.kv("eps2", eps2);
        J.kv("eps2_i", imax); J.kv("eps2_j", jmax);
        J.kv("eps2_x", g.x(imax)); J.kv("eps2_y", g.y(jmax));
        if (grids) {
            J.array("x", axis(g, 'x', stride));
            J.array("y", axis(g, 'y', stride));
            J.grid2d("v", sc.v, g, stride);
            J.grid2d("v0", sc.v0, g, stride);
            J.array("fine_x", axis(gf, 'x', stride));
            J.array("fine_y", axis(gf, 'y', stride));
            J.grid2d("fine_v", sf.v, gf, stride);
            J.grid2d("fine_v0", sf.v0, gf, stride);
        }
    }

    os.close();
    std::cerr << "OK: " << outpath << "\n";
    return 0;
}
