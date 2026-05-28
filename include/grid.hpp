// ============================================================================
//  grid.hpp — прямоугольная сетка (n,m) и сеточная функция v(i,j).
//      h=(b-a)/n, x_i=a+i*h, i=0..n;  k=(d-c)/m, y_j=c+j*k, j=0..m.
// ============================================================================
#ifndef POISSON_GRID_HPP
#define POISSON_GRID_HPP

#include <vector>

struct Grid {
    int n, m;
    double a, b, c, d;
    double h, k;

    Grid(int n_, int m_, double a_, double b_, double c_, double d_)
        : n(n_), m(m_), a(a_), b(b_), c(c_), d(d_) {
        h = (b - a) / n;
        k = (d - c) / m;
    }

    double x(int i) const { return a + i * h; }
    double y(int j) const { return c + j * k; }
};

struct Field {
    int n, m;
    std::vector<double> data;   // row-major: index = i*(m+1) + j

    Field(int n_, int m_) : n(n_), m(m_), data((n_ + 1) * (m_ + 1), 0.0) {}

    double&       operator()(int i, int j)       { return data[i * (m + 1) + j]; }
    const double& operator()(int i, int j) const { return data[i * (m + 1) + j]; }
};

#endif // POISSON_GRID_HPP
