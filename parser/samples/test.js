import fs from "fs";

function hello() {
  helper();
}

function helper() {
  console.log("hi");
}

class User {
  save() {
    helper();
  }
}
