package main

interface Service {
    fun run()
}

class App : Service {
    override fun run() {}
}

fun main() {
    val a = App()
    a.run()
}