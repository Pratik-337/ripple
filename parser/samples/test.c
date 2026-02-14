#include <stdio.h>

void helper() 
{
    printf("helper\n");
}

int add(int a, int b) 
{
    return a + b;
}

int main() 
{
    helper();
    int x = add(2, 3);
    printf("%d\n", x);
    return 0;
}
