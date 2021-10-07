import re
import time

def a_parse(expr:str, start = '(', end = ')'):
    def _helper(iter):
        items = []
        for item in iter:
            if item == start:
                result, closeparen = _helper(iter)
                if not closeparen:
                    raise ValueError("bad expression -- unbalanced parentheses")
                items.append(result)
            elif item == end:
                return items, True
            else:
                items.append(item)
        return items, False
    return _helper(iter(expr))[0]


def extract(inp:list):
    res = []
    result = {}
    parent = ""
    child = {}
    d = {}
    for item in inp: 
        if type(item) == str:
            parent += item
        elif type(item) == list:
            child = extract(item)
            result[parent] = child
            d[parent] = child
            res.append(d)
            d = {}
            parent = ""
    if not result:
        return parent
    return result
    

def handle(text):
    return extract(a_parse(text))
    
def test():
    u_in = input("Enter a String: ")
    while u_in: 
        handle(u_in)
        u_in = input("Enter a String: ")


if __name__ == "__main__": 
    print("RUNNING TEST")
    test()