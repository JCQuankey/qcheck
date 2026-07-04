# A common LLM mistake: uses execute() and Aer imports removed in Qiskit 1.0.
# This code will NOT run on modern Qiskit. qcheck should FAIL this.
from qiskit import QuantumCircuit, execute, Aer

qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cnot(0, 1)          # deprecated alias for .cx()
qc.measure([0, 1], [0, 1])

backend = Aer.get_backend("qasm_simulator")
result = execute(qc, backend, shots=1024).result()
print(result.get_counts())
