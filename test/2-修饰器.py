
def decorater(func):
    def wrapper():
        print("Hello, World!")
        func()
    return wrapper
@decorater
def say_hello():
    pass

#修饰器，就是在函数名上进行修饰，即将上面的返回函数修饰到下面的函数，通过返回这一内部操作得以调用内部函数

say_hello()

def repeat(n):
    def wrapper(func):
        def inner(*args,**kwargs):
            for _ in range(n):
                func()
            return inner
    return wrapper
@repeat
def say(name):
    print(f"Hi,{name}!")

say("Alice")