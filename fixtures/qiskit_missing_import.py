# LLMs frequently emit a circuit without importing QuantumCircuit.
qc = QuantumCircuit(2, 2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
