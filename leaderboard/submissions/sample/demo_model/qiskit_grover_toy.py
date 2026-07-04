# SAMPLE / DEMO submission — hand-written illustration, NOT a real model output.
# Task: qiskit_grover_toy. Expected qcheck verdict: UNSAFE
# (writes results to disk with open(...) — a filesystem side effect qcheck rejects).
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)
qc.h([0, 1])
qc.cz(0, 1)          # toy oracle
qc.h([0, 1])
qc.measure([0, 1], [0, 1])

with open("grover_result.txt", "w") as f:   # unsafe: filesystem access
    f.write("results here")
