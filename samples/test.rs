use std::fs;
use std::io;

fn helper() {
    println!("helper called");
}

fn main() {
    helper();
    read_file();
}

fn read_file() {
    let _data = fs::read_to_string("test.txt");
}
