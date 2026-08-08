
# connectors/universal_bridge.py - RATISS V9 Sovereign Universal Bridge
try:
    from schemas import Theory, Request
except ImportError:
    from connectors.schemas import Theory, Request

def route(theory: Theory) -> Request:
    theory_hash = theory.hash()
    print(f"[RATISS_BRIDGE] Routing {theory.name} -> {theory.target} | hash={theory_hash}")

    target = theory.target if theory.target else "CPU_LOCAL"
    target_upper = target.upper()

    if target_upper == "GPU_CUDA":
        try:
            from transformeurG import transform
        except ImportError:
            from connectors.transformeurG import transform
        return transform(theory)
    elif target_upper == "QPU_PHOTONIC":
        try:
            from transformeurQ import transform
        except ImportError:
            from connectors.transformeurQ import transform
        return transform(theory)
    else:
        try:
            from cpu_fallback import transform
        except ImportError:
            from connectors.cpu_fallback import transform
        return transform(theory)

class UniversalBridge:
    def route(self, theory: Theory) -> Request:
        return route(theory)

    def send(self, theory: Theory) -> Request:
        return route(theory)
