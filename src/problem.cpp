// ============================================================================
//  problem.cpp — функции задачи (вариант 2).
// ============================================================================
#include "problem.hpp"
#include <cmath>

namespace problem {

static const double PI = 3.14159265358979323846;

double u_exact(double x, double y) {
    return std::exp(1.0 - x * x - y * y);
}

double f_test(double x, double y) {
    return 4.0 * (1.0 - x * x - y * y) * std::exp(1.0 - x * x - y * y);
}

double mu1_test(double y) { return u_exact(A, y); }
double mu2_test(double y) { return u_exact(B, y); }
double mu3_test(double x) { return u_exact(x, C); }
double mu4_test(double x) { return u_exact(x, D); }

// d^4/dx^4 exp(1-x^2-y^2) = u*(16x^4 - 48x^2 + 12)  (полином Эрмита H4)
double u_d4x(double x, double y) {
    return u_exact(x, y) * (16.0 * x * x * x * x - 48.0 * x * x + 12.0);
}
double u_d4y(double x, double y) {
    return u_exact(x, y) * (16.0 * y * y * y * y - 48.0 * y * y + 12.0);
}

double f_main(double x, double y) {
    double s = std::sin(PI * x * y);
    return std::fabs(s * s * s);
}

double mu1_main(double y) { return 1.0 - y * y; }
double mu2_main(double y) { return 1.0 - y * y; }
double mu3_main(double x) { return std::fabs(std::sin(PI * x)); }
double mu4_main(double x) { return std::fabs(std::sin(PI * x)); }

} // namespace problem
