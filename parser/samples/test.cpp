#include <iostream>

class Calculator {
public:
    int add(int a, int b) {
        std::cout << "Adding\n";
        return a + b;
    }
};

int main() {
    Calculator calc;
    int result = calc.add(3, 4);
    std::cout << result << std::endl;
    return 0;
}
