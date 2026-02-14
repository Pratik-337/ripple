import fs from "fs";

function helper() {
    console.log("helper");
}

function main() {
    helper();
}

class User {
    save() {
        helper();
    }
}
