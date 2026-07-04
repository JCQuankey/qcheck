# SAMPLE / DEMO submission — hand-written illustration, NOT a real model output.
# Task: qiskit_bell_state. Expected qcheck verdict: PASS.
from qiskit import QuantumCircuit

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure([0, 1], [0, 1])
