import time

from sympy.physics.quantum.gate import H
from sympy.physics.quantum.qubit import Qubit

from quantpy.sympy.qapply import qapply
from quantpycupy.executor.cupy_executor import CupyExecutor

def test_hadamard_loop(printFlag=False):
    lp = 1  # loop size
    ms = 5
    me = 5
    for n in range(ms, me+1):
        ts = 5.0      # target second
        lc = lp       # loop counter
        ss = 0.0      # sum sec
        for l in range(lc):
            # print(n)
            p = '0' * n
            # print(p)
            q = Qubit(p)
            # print(q)
            h = H(0)
            for i in range(1,n):
                h = H(i) * h
            print(h)

            executor = CupyExecutor()
            start = time.time()
            r = qapply(h * q, executor=executor)
            elapsed_time = time.time() - start
            ss += elapsed_time
            if printFlag:
                print(r)
            print ("elapsed_time:\t{0},\t{1} [sec]".format(n,elapsed_time))

        print("average:\t{0}x{1},\t{2} [sec]".format(n, lc, ss/lc))
        assert ss/lc < ts

test_hadamard_loop()
