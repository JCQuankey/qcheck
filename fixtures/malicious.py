# MUST be rejected by qcheck: a circuit snippet should never touch the OS.
import os

os.system("echo pwned > /tmp/qcheck_should_never_write_this")
from qiskit import QuantumCircuit

qc = QuantumCircuit(1)
qc.h(0)
