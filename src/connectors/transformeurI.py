
# connectors/transformeurI.py
from .schemas import Theory, Query
from .ibm_client import IBMClient

try:
    from qiskit import QuantumCircuit
    QISKIT_AVAILABLE = True
except ImportError:
    QuantumCircuit = None
    QISKIT_AVAILABLE = False


class TransformerI:
    def __init__(self):
        self.client = IBMClient()

    def transform(self, theory: Theory) -> Query:
        platform = theory.parameters.get('platform', 'ibmq_qasm_simulator')
        shots = theory.parameters.get('shots', 1024)

        code = f"""from qiskit import QuantumCircuit
from connectors.ibm_client import IBMClient

client = IBMClient()
circuit = QuantumCircuit(2, 2)
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

results = client.run_circuit(circuit, shots={shots}, platform="{platform}")
print(results)
"""
        return Query(
            target="ibm",
            code=code,
            resources={
                "platform": platform,
                "shots": shots
            }
        )

    def execute(self, query: Query):
        platform = query.resources.get('platform', 'ibmq_qasm_simulator')
        shots = query.resources.get('shots', 1024)

        self.client.connect(platform)

        if QISKIT_AVAILABLE and QuantumCircuit is not None:
            circuit = QuantumCircuit(2, 2)
            circuit.h(0)
            circuit.cx(0, 1)
            circuit.measure([0, 1], [0, 1])
        else:
            circuit = None

        results = self.client.run_circuit(circuit, shots=shots, platform=platform)
        return {
            "status": "success",
            "platform": f"IBM Quantum ({platform})",
            "data": results,
            "shots": shots
        }
