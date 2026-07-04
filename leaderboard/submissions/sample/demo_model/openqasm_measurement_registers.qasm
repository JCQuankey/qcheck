// SAMPLE / DEMO submission - hand-written illustration, NOT a real model output.
// Task: openqasm_measurement_registers. Expected qcheck verdict: FAIL
// (measures qubit index 2 of a 2-qubit register - out of range / into undeclared bit).
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q[2] -> c[2];
