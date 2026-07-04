# SAMPLE / DEMO submission — hand-written illustration, NOT a real model output.
# Task: qiskit_teleportation_basic. Expected qcheck verdict: FAIL
# (uses execute() and Aer imports removed in Qiskit 1.0 — a common LLM mistake).
from qiskit import QuantumCircuit, execute, Aer

qc = QuantumCircuit(3, 3)
qc.h(1)
qc.cx(1, 2)
qc.cx(0, 1)
qc.h(0)
qc.measure([0, 1], [0, 1])

backend = Aer.get_backend("qasm_simulator")
result = execute(qc, backend, shots=1024).result()
print(result.get_counts())
