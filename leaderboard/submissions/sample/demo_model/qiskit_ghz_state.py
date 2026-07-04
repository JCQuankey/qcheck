# SAMPLE / DEMO submission — hand-written illustration, NOT a real model output.
# Task: qiskit_ghz_state. Expected qcheck verdict: PASS.
from qiskit import QuantumCircuit

qc = QuantumCircuit(3, 3)
qc.h(0)
qc.cx(0, 1)
qc.cx(1, 2)
qc.measure([0, 1, 2], [0, 1, 2])
