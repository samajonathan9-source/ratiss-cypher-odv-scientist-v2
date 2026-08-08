
# connectors/cpu_fallback.py - RATISS V9 Local CPU Fallback
try:
    from schemas import Theory, Request
except ImportError:
    from connectors.schemas import Theory, Request

def transform(theory: Theory) -> Request:
    code = f"# CPU fallback Ryzen 5 PRO 2500U - Lanczos ED 4x4 / 6x6 truncated - params={theory.params}"
    resources = {
        "target": "CPU_LOCAL",
        "cpu": "Ryzen 5 PRO 2500U"
    }

    return Request(
        theory_hash=theory.hash(),
        code=code,
        resources=resources
    )
