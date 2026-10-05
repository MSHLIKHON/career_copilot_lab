"""Conservative plagiarism guards for the practice workspace.

The browser cannot prove where submitted text came from.  This module therefore
blocks only strong, explainable matches with the task's own reference answer.
It intentionally does not compare one learner's private code with another's.
"""

import ast
import io
import tokenize
from difflib import SequenceMatcher


_PRESERVED_NAMES = {
    "solve", "abs", "len", "range", "sorted", "True", "False", "None"
}


def _tokens(source):
    """Return formatting/comment-independent source tokens."""
    try:
        stream = tokenize.generate_tokens(io.StringIO(source).readline)
        ignored = {
            tokenize.ENCODING, tokenize.ENDMARKER, tokenize.INDENT,
            tokenize.DEDENT, tokenize.NEWLINE, tokenize.NL, tokenize.COMMENT,
        }
        return tuple((item.type, item.string) for item in stream if item.type not in ignored)
    except (IndentationError, tokenize.TokenError):
        return ()


class _CanonicalNames(ast.NodeTransformer):
    """Make variable renaming irrelevant while preserving language names."""

    def __init__(self):
        self.names = {}

    def name(self, value):
        if value in _PRESERVED_NAMES:
            return value
        if value not in self.names:
            self.names[value] = f"learner_name_{len(self.names) + 1}"
        return self.names[value]

    def visit_arg(self, node):
        node.arg = self.name(node.arg)
        return node

    def visit_Name(self, node):
        node.id = self.name(node.id)
        return node


def _structure(source):
    try:
        tree = ast.parse(source)
    except (SyntaxError, RecursionError):
        return "", 0
    tree = _CanonicalNames().visit(tree)
    ast.fix_missing_locations(tree)
    return ast.dump(tree, annotate_fields=False, include_attributes=False), sum(1 for _ in ast.walk(tree))


def check_submission(source, task):
    """Return an explainable integrity decision for a practice submission.

    Exact matches ignore whitespace and comments.  Near-copy detection is used
    only for non-trivial programs and at a deliberately high similarity level to
    avoid rejecting ordinary short answers with only one natural implementation.
    """
    reference = task.get("solution", "")
    submitted_tokens = _tokens(source)
    reference_tokens = _tokens(reference)
    if submitted_tokens and submitted_tokens == reference_tokens:
        return {
            "blocked": True,
            "reason": "This submission matches the task's reference answer after comments and formatting are removed.",
            "kind": "reference_copy",
            "similarity": 1.0,
        }

    submitted_structure, submitted_nodes = _structure(source)
    reference_structure, reference_nodes = _structure(reference)
    similarity = 0.0
    if submitted_structure and reference_structure:
        similarity = SequenceMatcher(None, submitted_structure, reference_structure, autojunk=False).ratio()
    if min(submitted_nodes, reference_nodes) >= 28 and similarity >= 0.985:
        return {
            "blocked": True,
            "reason": "This submission is structurally almost identical to the reference answer, including after variable renaming.",
            "kind": "near_reference_copy",
            "similarity": round(similarity, 4),
        }
    return {"blocked": False, "reason": "", "kind": "clear", "similarity": round(similarity, 4)}
