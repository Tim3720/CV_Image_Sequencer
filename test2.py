
class A:
    def __init__(self):
        self.a = 0

class B(A):
    def __init__(self):
        super().__init__()

class C(B):
    def __init__(self):
        super().__init__()

class D(B):
    def __init__(self):
        super().__init__()


a = B()
c = C()
d = D()

print(issubclass(type(c), B))
print(issubclass(type(d), B))
