<?php

require_once "utils.php";

function helper() {
    echo "helper";
}

function main() {
    helper();
}

class User {
    public function save() {
        helper();
    }
}
