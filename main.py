from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sympy import Matrix, lcm
import re

app = FastAPI()

# ✅ Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # puedes restringirlo a ["http://127.0.0.1:5500"] si usas Live Server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# MODELO Y VARIABLES
# -------------------------
class Equation(BaseModel):
    equation: str

historial = []  # Guardar ecuaciones balanceadas en memoria


# -------------------------
# FUNCIÓN DE PARSEO Y BALANCEO
# -------------------------
def parse_formula(formula):
    """Convierte una fórmula química en diccionario de {elemento: cantidad}"""
    tokens = re.findall(r'([A-Z][a-z]?)(\d*)', formula)
    composition = {}
    for (element, count) in tokens:
        count = int(count) if count else 1
        composition[element] = composition.get(element, 0) + count
    return composition

def balance_equation(equation: str):
    """Balancea una ecuación química del tipo H2 + O2 = H2O"""
    left_side, right_side = equation.split("=")
    left_compounds = [x.strip() for x in left_side.split("+")]
    right_compounds = [x.strip() for x in right_side.split("+")]

    # Obtener todos los elementos únicos
    elements = set()
    for compound in left_compounds + right_compounds:
        elements.update(parse_formula(compound).keys())
    elements = sorted(elements)

    # Construir matriz para sistema de ecuaciones lineales
    matrix = []
    for element in elements:
        row = []
        for compound in left_compounds:
            row.append(parse_formula(compound).get(element, 0))
        for compound in right_compounds:
            row.append(-parse_formula(compound).get(element, 0))
        matrix.append(row)

    M = Matrix(matrix)
    null_space = M.nullspace()
    if not null_space:
        raise ValueError("No se pudo balancear la ecuación.")

    # ✅ Convertir solución en coeficientes enteros
    coeffs = null_space[0]
    denominadores = [c.q for c in coeffs]  # extraer denominadores
    factor = lcm(denominadores)  # mínimo común múltiplo
    coeffs = [int(c * factor) for c in coeffs]

    # Construir ecuación balanceada
    left = " + ".join(f"{coeffs[i]} {left_compounds[i]}" for i in range(len(left_compounds)))
    right = " + ".join(f"{coeffs[i+len(left_compounds)]} {right_compounds[i]}" for i in range(len(right_compounds)))
    return f"{left} = {right}"


# -------------------------
# ENDPOINTS
# -------------------------
@app.post("/balance")
def balancear(eq: Equation):
    try:
        ecuacion = eq.equation.replace("->", "=").strip()  # Cambiar -> por =
        balanceada = balance_equation(ecuacion)
        historial.append({"original": ecuacion, "balanceada": balanceada})
        return {"balanced": balanceada}
    except Exception as e:
        return {"error": str(e)}

@app.get("/history")
def get_history():
    return historial
