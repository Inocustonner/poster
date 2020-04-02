import sys

from prompt_toolkit import prompt
from ShellFs import ShellFs
import interactive_libs

@ShellFs.func
def q():
   sys.exit()

def main():
   while True:
      inp = prompt('>> ').split()
      getattr(ShellFs, inp[0], 
         lambda *args, **kwargs: print("No function found"))(inp[1:])

if __name__ == "__main__":
   main()