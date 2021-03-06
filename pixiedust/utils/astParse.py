# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2017
# 
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------

import ast
import inspect
from astunparse import unparse

def get_caller_text(frame):
    """
    Return the expression that calls the frame
    """
    def find_match_node(node):
        "Find a candidate ast node"
        match_node = None
        for chd in ast.iter_child_nodes(node):
            if getattr(chd, "lineno", 0) > frame.f_back.f_lineno:
                break
            match_node = node if isinstance(chd, ast.Name) and isinstance(node, ast.Call) and chd.id == frame.f_code.co_name else match_node
            match_node = find_match_node(chd) or match_node
        return match_node
    lines, _ = inspect.findsource(frame.f_back.f_code)
    match_node = find_match_node(ast.parse("".join(lines)))
    return unparse(match_node).strip().replace(', ', ',') if match_node is not None else None

def parse_function_call(expression):
    """
    Parse an expression looking for a function call
    return a dictionary with function name, args and kwargs
    e.g:
    {
        'func': 'display',
        'args': ['df'],
        'kwargs': {
            'aggregation': "'SUM'",
            'nostore_cw': "'1098'",
            'rowCount': "'500'"
        }
    }
    """
    class Walker(ast.NodeVisitor):
        "ast NodeVisition helper class"
        def __init__(self):
            self.results = {'func': None, 'args': [], 'kwargs': {}}

        def visit_Call(self, node):
            "Visit the first call function"
            if self.results['func'] is not None:
                return
            self.results['func'] = node.func.id
            self.results['args'] = [unparse(arg).strip() for arg in node.args]
            self.results['kwargs'] = {kw.arg:unparse(kw.value).strip().strip('\'"') for kw in node.keywords}
    walker = Walker()
    walker.visit(ast.parse(expression))
    return walker.results