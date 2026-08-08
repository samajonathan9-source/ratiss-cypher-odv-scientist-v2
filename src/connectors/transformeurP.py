
# connectors/transformeurP.py
from .schemas import Theory, Query
from .pennylane_bridge import PennyLaneBridge, PENNYLANE_AVAILABLE


class TransformerP:
    def __init__(self):
        self.bridge = PennyLaneBridge()

    def transform(self, theory: Theory) -> Query:
        wires = int(theory.parameters.get('wires', 2))
        shots = int(theory.parameters.get('shots', 1000))
        params = theory.parameters.get('params', [0.54, 0.12, 0.88])

        code = f"""import pennylane as qml

dev = qml.device('default.qubit', wires={wires}, shots={shots})

@qml.qnode(dev)
def circuit():
    qml.Hadamard(wires=0)
    qml.CNOT(wires=[0, 1])
    return qml.probs(wires=list(range({wires})))

probs = circuit()
print(probs)
"""
        return Query(
            target="pennylane",
            code=code,
            resources={
                "wires": wires,
                "shots": shots,
                "params": params,
                "platform": theory.parameters.get('platform', 'default.qubit')
            }
        )

    def execute(self, query: Query):
        wires = query.resources.get('wires', 2)
        shots = query.resources.get('shots', 1000)
        params = query.resources.get('params')

        if params:
            results = self.bridge.execute_variational_circuit(params=params, wires=wires, shots=shots)
        else:
            results = self.bridge.execute_bell_state(wires=wires, shots=shots)

        return {
            "status": "success",
            "platform": f"PennyLane ({query.resources.get('platform', 'default.qubit')})",
            "data": results,
            "shots": shots,
            "pennylane_native": PENNYLANE_AVAILABLE
        }
