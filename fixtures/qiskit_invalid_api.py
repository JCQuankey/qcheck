# Classic stale-LLM output: execute() and Aer were removed from qiskit in 1.0.
from qiskit import QuantumCircuit, Aer, execute

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cnot(0, 1)
qc.measure([0, 1], [0, 1])
result = execute(qc, Aer.get_backend("qasm_simulator")).result()
