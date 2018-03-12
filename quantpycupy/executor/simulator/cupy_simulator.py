
"""
class of quantum circuit simulator
"""

import numpy as np

import cupy as cp
from quantpycupy.executor.simulator.cupy_kernel import KernelList as qcgate

class CupySimulator():
    def __init__(self,verbose=False):
        """
        @param n : number of qubit
        @param verbose : output verbose comments for debug (default: false)
        @return None
        """
        self.verbose = verbose
        self.currentTrace = None
        self.basis_gates = ["cx","m0","m1"]

    def initialize(self,n):
        self.n = n
        self.dim = 2**n
        self.state = cp.zeros(self.dim,dtype=np.complex128)
        self.state[0]=1.
        self.nstate = cp.zeros_like(self.state)

    def apply(self,gate,target,control=None,theta=None,param=None,update=True):
    #def apply(self,gate,ind1,ind2=None,ind3=None,theta=None,update=True):
        """
        apply quantum gate to the qubit(s)

        @param gate : string or cupy kernel of applying gate
        @param ind1 : qubit index 1
        @param ind2 : qubit index 2, used in two qubit gate (default: None)
        @param ind3 : qubit index 3, used in three qubit gate (default: None)
        @param theta : rotation angle, used in rotation gate (default: None)
        @update : The calculated state is placed in buffer-state. If update is Ture, swap current state with buffer after calculation. (default: True)
        """
        ind1 = target
        ind2 = control
        gate = self.__getGateInstance(gate)
        gateName = gate.name

        if(gate in qcgate.oneGate):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            self.nstate = gate(self.state,ind1,self.nstate)
            if(self.verbose): print("Apply onequbit gate {} to {}-th qubit".format(gateName,ind1))
        elif(gate in qcgate.twoGate):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            if(ind2 is None): raise IndexError("ind2 is not specified in "+gateName)
            if(not self.__bound(ind2)): raise IndexError("ind2 is out of range in "+gateName)
            self.nstate = gate(self.state,ind1,ind2,self.nstate)
            if(self.verbose): print("Apply twoqubit gate {} to ({},{})-th qubit".format(gateName,ind1,ind2))
        elif(gate in qcgate.threeGate):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            if(ind2 is None): raise IndexError("ind2 is not specified in "+gateName)
            if(not self.__bound(ind2)): raise IndexError("ind2 is out of range in "+gateName)
            if(ind3 is None): raise IndexError("ind3 is not specified in "+gateName)
            if(not self.__bound(ind3)): raise IndexError("ind3 is out of range in "+gateName)
            self.nstate = gate(self.state,ind1,ind2,ind3,self.nstate)
            if(self.verbose): print("Apply threequbit gate {} to ({},{},{})-th qubit".format(gateName,ind1,ind2,ind3))
        elif(gate in qcgate.oneRot):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            if(theta is None): raise IndexError("theta is not specified in "+gateName)
            self.nstate = gate(self.state,ind1,theta,self.nstate)
            if(self.verbose): print("Rotate {}-th qubit {} with {} operator".format(ind1,theta,gateName))
        elif(gate in qcgate.twoRot):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            if(ind2 is None): raise IndexError("ind2 is not specified in "+gateName)
            if(not self.__bound(ind2)): raise IndexError("ind2 is out of range in "+gateName)
            if(theta is None): raise IndexError("theta is not specified in "+gateName)
            self.nstate = gate(self.state,ind1,ind2,theta,self.nstate)
            if(self.verbose): print("Rotate ({},{})-th qubit {} with {} operator".format(ind1,ind2,theta,gateName))
        elif(gate in qcgate.measurement):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            self.nstate = gate(self.state,ind1,self.nstate)
            if(self.verbose): print("Measurement {}-th qubit with {}".format(ind1,gateName))
            self.currentTrace = None
        elif(gate in [qcgate.ker_U]):
            if(not self.__bound(ind1)): raise IndexError("ind1 is out of range in "+gateName)
            #print(theta)
            self.nstate = gate(self.state,ind1,param[0],param[1],param[2],self.nstate)
            if(self.verbose): print("Generic unitary ({},{},{}) on {}-th qubit with {}".format(param[0],param[1],param[2],ind1,gateName))
            self.currentTrace = None
        else:
            raise Exception("not implemented {}".format())

        if(update):
            self.update()
        else:
            return self.trace(buffer=True)

    def update(self):
        """
        swap buffer-state with the current state
        """
        self.state,self.nstate = self.nstate,self.state
        self.currentTrace = None

    def trace(self,buffer=False):
        """
        take trace of the quantum state
        @buffer : calculate trace of buffer-state (default: False)
        """
        if(self.verbose): print("Calculate trace")
        if(buffer):
            return np.real(cp.asnumpy(qcgate.ker_trace(self.nstate)))
        else:
            val = qcgate.ker_trace(self.state)
            self.currentTrace = val
            return np.real(cp.asnumpy(val))

    def normalize(self,eps=1e-16):
        """
        normalize quantum state
        @eps : if trace is smaller than eps, raise error for avoiding Nan (default: 1e-16)
        """
        if(self.currentTrace is None):
            self.trace()
        valtrace = np.real(cp.asnumpy(self.currentTrace))
        if(valtrace<eps):
            raise ValueError("Trace is too small : {}".format(valtrace))
        self.state/=cp.sqrt(self.currentTrace)
        if(self.verbose): print("Normalize")

    def asnumpy(self):
        """
        recieve quantum state as numpy matrix.
        Do nothing in numpy
        """
        return cp.asnumpy(self.state)

    def __str__(self,eps=1e-10):
        """
        overload string function
        return bra-ket representation of current quantum state (very slow when n is large)
        """
        fst = True
        ret = ""
        for ind in range(self.dim):
            val = self.state[ind]
            if(abs(val)<eps):
                continue
            else:
                if(fst):
                    fst = False
                else:
                    ret += " + "
                ret += str(val) + "|" + format(ind,"b").zfill(self.n)[::-1]+ ">"
        return ret

    def __bound(self,ind):
        return (0<=ind and ind<self.n)

    def __getGateInstance(self,gate):
        """
        converting string representation of gate to gate instance. do nothing for gate instance
        @param gate : string or gate instance
        @return : gate instance
        """
        if(type(gate)==str or type(gate)==np.str_):
            if(gate not in qcgate.allGateName):
                raise NameError("Unknown gate string "+ gate +" : defined gates are ",str(qcgate.allGateName))
            else:
                gateInd = qcgate.allGateName.index(gate)
                gate = qcgate.allGate[gateInd]
        else:
            if(gate not in qcgate.allGate):
                raise ValueError("Unknown gate instance")
        return gate

    def can_simulate_gate(self,gateName):
        return gateName in qcgate.allGateName 
