import java.util.List

class UserService 
{
    fun hello() 
    {
        helper()
    }
    private fun helper() 
    {
        println("Hello from Kotlin")
    }
    fun add(a: Int, b: Int): Int 
    {
        return a + b
    }
}
