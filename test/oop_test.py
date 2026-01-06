class A:
    def __init__(self, a: int):
        self.a = a
    def __private_method(self):
        print(self.a)


class B(A): 
    def __init__(self, a: int):
        super().__init__(a)
    
b = B(10)

b.__private_method()
