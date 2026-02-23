trait Service {
    fn run();
}

struct App;

impl Service for App {
    fn run() {}
}

fn main() {
    let a = App;
    a.run();
}