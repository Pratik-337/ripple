class MyJsService {
  constructor() {
    this.data = "JS Service Data";
  }

  getData() {
    return this.data;
  }
}

function runJsExample() {
  // Local variable declaration
  let serviceInstance = new MyJsService();
  
  // Call on local variable
  serviceInstance.getData();
}

// Another example with a class method
class MyJsApp {
  constructor() {
    this.appService = new MyJsService(); // Field-like property
  }

  runApp() {
    this.appService.getData(); // Call on field-like property
    
    let anotherService = new MyJsService(); // Another local variable
    anotherService.getData(); // Call on another local variable
  }
}