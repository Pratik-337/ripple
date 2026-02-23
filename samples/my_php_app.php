<?php
require_once 'my_php_lib.php';

function mainApp() {
    $service = new MyPhpService();
    $service->doWork();
    globalPhpFunction();
}

mainApp();
