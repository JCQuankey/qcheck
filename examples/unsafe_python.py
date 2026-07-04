# A quantum snippet should never touch the OS. qcheck should mark this UNSAFE
# (exit code 2) and refuse to analyze it further. qcheck never executes it.
import os
from qiskit import QuantumCircuit

os.system("echo this-should-never-run")   # filesystem/process access -> unsafe

qc = QuantumCircuit(1)
qc.h(0)
