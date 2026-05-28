// ============================================================================
//  problem.hpp — задача Дирихле для Пуассона, вариант 2, область [-1,1]^2.
//  Уравнение Δu = -f.
//  Тест:    u* = exp(1-x^2-y^2),  f* = 4(1-x^2-y^2)exp(1-x^2-y^2) = -Δu*.
//  Основная: f = |sin^3(pi x y)|,  mu1=mu2=1-y^2,  mu3=mu4=|sin(pi x)|.
// ============================================================================
#ifndef POISSON_PROBLEM_HPP
#define POISSON_PROBLEM_HPP

namespace problem {

constexpr int    VARIANT = 2;
constexpr double A = -1.0;
constexpr double B =  1.0;
constexpr double C = -1.0;
constexpr double D =  1.0;

double u_exact(double x, double y);
double f_test(double x, double y);
double mu1_test(double y);
double mu2_test(double y);
double mu3_test(double x);
double mu4_test(double x);

// d^4 u*/dx^4, d^4 u*/dy^4 — для оценки погрешности схемы (теорема 7.7)
double u_d4x(double x, double y);
double u_d4y(double x, double y);

double f_main(double x, double y);
double mu1_main(double y);
double mu2_main(double y);
double mu3_main(double x);
double mu4_main(double x);

} // namespace problem

#endif // POISSON_PROBLEM_HPP
