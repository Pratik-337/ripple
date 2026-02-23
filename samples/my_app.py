# In samples/my_app.py
from my_service import MyService

class MyApp:
    def __init__(self):
        # Test field resolution
        self.service_field = MyService()

    def run_field(self):
        self.service_field.do_work()

    def run_local(self):
        # Test local variable resolution
        local_service = MyService()
        local_service.do_work()

def main():
    app = MyApp()
    app.run_field()
    app.run_local()