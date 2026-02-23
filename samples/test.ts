class MyTsService {
  private data: string;

  constructor() {
    this.data = "TS Service Data";
  }

  public getData(): string {
    return this.data;
  }
}

function runTsExample() {
  // Local variable declaration with type annotation
  let serviceInstance: MyTsService = new MyTsService();
  
  // Call on local variable
  serviceInstance.getData();
}

class MyTsApp {
  private appService: MyTsService; // Field with type annotation

  constructor() {
    this.appService = new MyTsService();
  }

  public runApp(): void {
    this.appService.getData(); // Call on field
  }
}