#!/usr/bin/env python3
import sys
from calculator.calc import add,sub,mul,div

def main():
    if len(sys.argv)!=4:
        print('Usage: calc <op> <a> <b>')
        sys.exit(2)
    op=sys.argv[1]
    a=float(sys.argv[2])
    b=float(sys.argv[3])
    if op=='add':
        print(add(a,b))
    elif op=='sub':
        print(sub(a,b))
    elif op=='mul':
        print(mul(a,b))
    elif op=='div':
        try:
            print(div(a,b))
        except Exception as e:
            print('Error:',e)
            sys.exit(1)
    else:
        print('Unknown op')
        sys.exit(2)

if __name__=='__main__':
    main()
