
import ast
import copy
import math
import operator


class RunnerError(Exception):
    pass


class Returned(Exception):
    def __init__(self, value):
        self.value = value


class BreakLoop(Exception):
    pass


class ContinueLoop(Exception):
    pass


BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
       ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod}
CMP = {ast.Eq: operator.eq, ast.NotEq: operator.ne, ast.Lt: operator.lt,
       ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
       ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b,
       ast.Is: operator.is_, ast.IsNot: operator.is_not}
ALLOWED = (ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
           ast.Assign, ast.AugAssign, ast.Expr, ast.If, ast.For, ast.While,
           ast.Break, ast.Continue, ast.Pass, ast.Name, ast.Constant, ast.List,
           ast.Tuple, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare, ast.Call,
           ast.Subscript, ast.Slice, ast.IfExp, ast.Load, ast.Store,
           ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.USub,
           ast.UAdd, ast.Not, ast.And, ast.Or, *CMP.keys())
BUILTINS = {"len", "range", "sum", "min", "max", "abs", "sorted", "reversed",
            "list", "int", "str", "bool", "enumerate", "round"}


def validate(source):
    if not isinstance(source, str) or len(source) > 12000:
        raise RunnerError("Code must be text with at most 12,000 characters.")
    tree = ast.parse(source)
    if sum(1 for _ in ast.walk(tree)) > 1800:
        raise RunnerError("Code is too complex for this teaching runner.")
    functions = {}
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if not isinstance(node, ast.FunctionDef):
            raise RunnerError("Write function definitions only. No top-level calls, imports or input().")
        if node.name in functions or node.name in BUILTINS:
            raise RunnerError("Function names must be unique and cannot replace built-ins.")
        if node.decorator_list or node.args.defaults or node.args.kw_defaults or node.args.kwonlyargs or node.args.vararg or node.args.kwarg or node.args.posonlyargs:
            raise RunnerError("Use simple positional function parameters only.")
        functions[node.name] = node
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise RunnerError(f"Unsupported Python feature: {type(node).__name__}. See Runner help.")
        if isinstance(node, (ast.Name, ast.arg, ast.FunctionDef)):
            name = getattr(node, "id", getattr(node, "arg", getattr(node, "name", "")))
            if name.startswith("_"):
                raise RunnerError("Private names are not supported.")
        if isinstance(node, ast.Call) and (not isinstance(node.func, ast.Name) or node.keywords):
            raise RunnerError("Only named function calls with positional arguments are supported.")
    return functions


class Interpreter:
    def __init__(self, source, budget=15000):
        self.functions = validate(source)
        self.left = budget
        self.depth = 0

    def tick(self):
        self.left -= 1
        if self.left <= 0:
            raise RunnerError("Step limit reached. Check for an infinite loop or too much work.")

    def guard(self, value, depth=0):
        self.tick()
        if depth > 12:
            raise RunnerError("Value nesting limit exceeded.")
        if isinstance(value, (list, tuple, str, range)):
            if len(value) > 1500:
                raise RunnerError("Collection limit exceeded (1,500 items).")
            if isinstance(value, (list, tuple)):
                for item in value:
                    self.guard(item, depth + 1)
        elif isinstance(value, (int, float)):
            if abs(value) > 10**15 or (isinstance(value, float) and not math.isfinite(value)):
                raise RunnerError("Number limit exceeded.")
        elif value is not None:
            raise RunnerError("Unsupported value type.")
        return value

    def binary(self, op, a, b):
        if isinstance(op, ast.Mult):
            for seq, count in ((a, b), (b, a)):
                if isinstance(seq, (str, list, tuple)) and isinstance(count, int) and len(seq) * max(count, 0) > 1500:
                    raise RunnerError("Collection limit exceeded.")
        if isinstance(op, ast.Add) and isinstance(a, (str, list, tuple)) and isinstance(b, type(a)) and len(a) + len(b) > 1500:
            raise RunnerError("Collection limit exceeded.")
        return self.guard(BIN[type(op)](a, b))

    def call(self, name, args):
        self.tick()
        for arg in args:
            self.guard(arg)
        if name in self.functions:
            if self.depth >= 30:
                raise RunnerError("Function call depth limit reached.")
            fn = self.functions[name]
            if len(args) != len(fn.args.args):
                raise RunnerError(f"{name} expects {len(fn.args.args)} arguments.")
            env = dict(zip([a.arg for a in fn.args.args], args))
            self.depth += 1
            try:
                self.block(fn.body, env)
            except Returned as result:
                return self.guard(result.value)
            finally:
                self.depth -= 1
            return None
        if name not in BUILTINS:
            raise RunnerError(f"Function '{name}' is not allowed or defined.")
        if name == "range":
            return self.guard(range(*args))
        builtins = {"len": len, "sum": sum, "min": min, "max": max, "abs": abs,
                    "sorted": sorted, "reversed": lambda x: list(reversed(x)),
                    "list": list, "int": int, "str": str, "bool": bool,
                    "enumerate": lambda x: list(enumerate(x)), "round": round}
        return self.guard(builtins[name](*args))

    def expr(self, node, env):
        self.tick()
        if isinstance(node, ast.Constant):
            return self.guard(node.value)
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise RunnerError(f"Variable '{node.id}' is not defined.")
            return env[node.id]
        if isinstance(node, (ast.List, ast.Tuple)):
            values = [self.expr(x, env) for x in node.elts]
            return self.guard(tuple(values) if isinstance(node, ast.Tuple) else values)
        if isinstance(node, ast.BinOp):
            return self.binary(node.op, self.expr(node.left, env), self.expr(node.right, env))
        if isinstance(node, ast.UnaryOp):
            value = self.expr(node.operand, env)
            return self.guard({ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}[type(node.op)](value))
        if isinstance(node, ast.Compare):
            a = self.expr(node.left, env)
            for op, rhs in zip(node.ops, node.comparators):
                b = self.expr(rhs, env)
                if not CMP[type(op)](a, b):
                    return False
                a = b
            return True
        if isinstance(node, ast.BoolOp):
            value = None
            for sub in node.values:
                value = self.expr(sub, env)
                if isinstance(node.op, ast.And) and not value:
                    break
                if isinstance(node.op, ast.Or) and value:
                    break
            return value
        if isinstance(node, ast.IfExp):
            return self.expr(node.body if self.expr(node.test, env) else node.orelse, env)
        if isinstance(node, ast.Slice):
            return slice(*(self.expr(x, env) if x else None for x in (node.lower, node.upper, node.step)))
        if isinstance(node, ast.Subscript):
            return self.guard(self.expr(node.value, env)[self.expr(node.slice, env)])
        if isinstance(node, ast.Call):
            return self.call(node.func.id, [self.expr(x, env) for x in node.args])
        raise RunnerError(f"Unsupported expression: {type(node).__name__}")

    def assign(self, target, value, env):
        self.guard(value)
        if isinstance(target, ast.Name):
            env[target.id] = value
        elif isinstance(target, (ast.Tuple, ast.List)):
            if len(target.elts) != len(value):
                raise RunnerError("Unpacking length mismatch.")
            for sub, item in zip(target.elts, value):
                self.assign(sub, item, env)
        elif isinstance(target, ast.Subscript):
            seq = self.expr(target.value, env)
            idx = self.expr(target.slice, env)
            if not isinstance(seq, list) or not isinstance(idx, int):
                raise RunnerError("Only integer list item assignment is supported.")
            if isinstance(value, (list, tuple)):
                raise RunnerError("Nested collection assignment is not supported.")
            seq[idx] = value
        else:
            raise RunnerError("Unsupported assignment target.")

    def block(self, statements, env):
        for node in statements:
            self.tick()
            if isinstance(node, ast.Return):
                raise Returned(self.expr(node.value, env) if node.value else None)
            elif isinstance(node, ast.Assign):
                value = self.expr(node.value, env)
                for target in node.targets:
                    self.assign(target, value, env)
            elif isinstance(node, ast.AugAssign):
                self.assign(node.target, self.binary(node.op, self.expr(node.target, env), self.expr(node.value, env)), env)
            elif isinstance(node, ast.Expr):
                self.expr(node.value, env)
            elif isinstance(node, ast.If):
                self.block(node.body if self.expr(node.test, env) else node.orelse, env)
            elif isinstance(node, (ast.For, ast.While)):
                broken = False
                iterator = iter(self.expr(node.iter, env)) if isinstance(node, ast.For) else None
                while True:
                    self.tick()
                    if iterator is not None:
                        try:
                            value = next(iterator)
                        except StopIteration:
                            break
                        self.assign(node.target, value, env)
                    elif not self.expr(node.test, env):
                        break
                    try:
                        self.block(node.body, env)
                    except ContinueLoop:
                        continue
                    except BreakLoop:
                        broken = True
                        break
                if not broken:
                    self.block(node.orelse, env)
            elif isinstance(node, ast.Break):
                raise BreakLoop()
            elif isinstance(node, ast.Continue):
                raise ContinueLoop()
            elif not isinstance(node, ast.Pass):
                raise RunnerError("Nested functions are not supported.")


def run_tests(source, task):
    try:
        functions = validate(source)
        if task["function"] not in functions:
            raise RunnerError(f"Keep the required function name: {task['function']}")
    except (SyntaxError, RunnerError, RecursionError) as error:
        return {"status": "syntax_error" if isinstance(error, SyntaxError) else "unsupported",
                "message": str(error), "passed": 0, "total": len(task["tests"]), "cases": []}
    cases = []
    for test in task["tests"]:
        try:
            result = Interpreter(source).call(task["function"], copy.deepcopy(test["args"]))
            ok = type(result) == type(test["expected"]) and result == test["expected"]
            if isinstance(result, float) and isinstance(test["expected"], (int, float)):
                ok = math.isclose(result, test["expected"], rel_tol=1e-7, abs_tol=1e-7)
            cases.append({**test, "actual": result, "passed": ok, "error": ""})
        except Exception as error:
            cases.append({**test, "actual": None, "passed": False, "error": f"{type(error).__name__}: {error}"})
    passed = sum(c["passed"] for c in cases)
    return {"status": "passed" if passed == len(cases) else "failed", "message": "",
            "passed": passed, "total": len(cases), "cases": cases}
