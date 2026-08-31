import os
from os.path import dirname, join

def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()
def create_rst():
    files = read_file("exclude.txt").split("\n")
    exclude = ' '.join(files)
    #print("sphinx-apidoc -o source ../ "+str(exclude))
    os.system("sphinx-apidoc -o source ../ "+str(exclude))

if __name__ == '__main__':
    create_rst()