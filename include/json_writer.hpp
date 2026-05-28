// ============================================================================
//  json_writer.hpp — минимальный генератор JSON (числа, строки, 1D/2D массивы).
// ============================================================================
#ifndef POISSON_JSON_WRITER_HPP
#define POISSON_JSON_WRITER_HPP

#include "grid.hpp"
#include <ostream>
#include <string>
#include <vector>
#include <iomanip>
#include <cmath>

class Json {
    std::ostream& os;
    bool first = true;

    void comma() { if (!first) os << ",\n"; first = false; }
    void num(double v) {
        if (std::isnan(v))      os << "null";
        else if (std::isinf(v)) os << (v > 0 ? "1e308" : "-1e308");
        else                    os << std::setprecision(17) << v;
    }
public:
    explicit Json(std::ostream& o) : os(o) { os << "{\n"; }
    ~Json() { os << "\n}\n"; }

    void kv(const std::string& key, double v)      { comma(); os << '"' << key << "\": "; num(v); }
    void kv(const std::string& key, int v)         { comma(); os << '"' << key << "\": " << v; }
    void kv(const std::string& key, const std::string& v) {
        comma(); os << '"' << key << "\": \"" << v << '"';
    }

    void array(const std::string& key, const std::vector<double>& a) {
        comma(); os << '"' << key << "\": [";
        for (size_t i = 0; i < a.size(); ++i) { if (i) os << ", "; num(a[i]); }
        os << "]";
    }

    // M[j][i] = field(i,j): строка = y, столбец = x
    void grid2d(const std::string& key, const Field& f, const Grid& g, int stride = 1) {
        comma(); os << '"' << key << "\": [\n";
        bool fj = true;
        for (int j = 0; j <= g.m; j += stride) {
            if (!fj) os << ",\n"; fj = false;
            os << "  [";
            bool fi = true;
            for (int i = 0; i <= g.n; i += stride) {
                if (!fi) os << ", "; fi = false;
                num(f(i, j));
            }
            os << "]";
        }
        os << "\n]";
    }
};

#endif // POISSON_JSON_WRITER_HPP
