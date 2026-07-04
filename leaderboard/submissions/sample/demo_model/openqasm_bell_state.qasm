// SAMPLE / DEMO submission - hand-written illustration, NOT a real model output.
// Task: openqasm_bell_state. Expected qcheck verdict: PASS.
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
creg c[2];
h q[0];
cx q[0], q[1];
measure q -> c;
