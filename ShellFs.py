import argparse

class MyNamespace:
    pass
    def empty(self):
        return not bool(vars(self))

class FunctionCaller:
    def __init__(self, func):
        self.func = func
        self.parser = argparse.ArgumentParser()

    def add_arg(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def __call__(self, *args):
        try:
            ns = MyNamespace()
            parsed_args = self.parser.parse_known_args(*args, namespace=ns)   
            if ns.empty():
                return self.func(*parsed_args[1])

            elif parsed_args[1]:
                return self.func(*parsed_args[1], **vars(parsed_args[0]))

            else:
                return self.func(**vars(parsed_args[0]))
        except Exception as e:
            print(e)
            return None

class ShellFs:
    """
        Function class is used to store in it functions as attributes.
        To add function to ShellFs use decorator @ShellFs.func
        To add arguments for the functions use @ShellFs.argument with parameters as for argsparse.ArgumentParser.add_argument
        NOTE: you can use @ShellFs.func and @ShellFs.argument in any order
    """

    funcs = {} # variable that stores FunctionCallers
    def __init__(self):
        pass

    @staticmethod
    def func(inp_func):
        if not ShellFs.funcs.get(inp_func.__name__ ):
            ShellFs.funcs.update({inp_func.__name__  : FunctionCaller(inp_func)})

        func_caller = ShellFs.funcs.get(inp_func.__name__ )
        setattr(ShellFs, inp_func.__name__ , staticmethod(func_caller))
        return inp_func
    
    @staticmethod
    def argument(*args, **kwargs):
        def decorator_argument(inp_func):
            if not ShellFs.funcs.get(inp_func.__name__ ):
                ShellFs.funcs.update({inp_func.__name__  : FunctionCaller(inp_func)})

            func_caller = ShellFs.funcs.get(inp_func.__name__ )
            func_caller.add_arg(*args, **kwargs)
            return inp_func

        return decorator_argument