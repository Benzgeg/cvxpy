"""
Copyright 2013 Steven Diamond

This file is part of CVXPY.

CVXPY is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CVXPY is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CVXPY.  If not, see <http://www.gnu.org/licenses/>.
"""

import cvxpy.lin_ops.lin_op as lo
from cvxpy.lin_ops.lin_constraints import LinEqConstr, LinLeqConstr
import cvxpy.interface as intf
import numpy as np

# Utility functions for dealing with LinOp.

class Counter(object):
    """A counter for ids.

    Attributes
    ----------
    count : int
        The current count.
    """
    def __init__(self):
        self.count = 0

ID_COUNTER = Counter()

def get_id():
    """Returns a new id and updates the id counter.

    Returns
    -------
    int
        A new id.
    """
    new_id = ID_COUNTER.count
    ID_COUNTER.count += 1
    return new_id

def create_var(size, var_id=None):
    """Creates a new internal variable.

    Parameters
    ----------
    size : tuple
        The (rows, cols) dimensions of the variable.
    var_id : int
        The id of the variable.

    Returns
    -------
    LinOP
        A LinOp representing the new variable.
    """
    if var_id is None:
        var_id = get_id()
    return lo.LinOp(lo.VARIABLE, size, [], var_id)

def create_param(value, size):
    """Wraps a parameter.

    Parameters
    ----------
    value : CVXPY Expression
        A function of parameters.
    size : tuple
        The (rows, cols) dimensions of the operator.

    Returns
    -------
    LinOP
        A LinOp wrapping the parameter.
    """
    return lo.LinOp(lo.PARAM, size, [], value)

def create_const(value, size):
    """Wraps a constant.

    Parameters
    ----------
    value : scalar, NumPy matrix, or SciPy sparse matrix.
        The numeric constant to wrap.
    size : tuple
        The (rows, cols) dimensions of the constant.

    Returns
    -------
    LinOP
        A LinOp wrapping the constant.
    """
    # Check if scalar.
    if intf.is_scalar(value):
        op_type = lo.SCALAR_CONST
    # Check if sparse.
    elif intf.is_sparse(value):
        op_type = lo.SPARSE_CONST
    else:
        op_type = lo.DENSE_CONST
    return lo.LinOp(op_type, size, [], value)

def sum_expr(operators):
    """Add linear operators.

    Parameters
    ----------
    operators : list
        A list of linear operators.

    Returns
    -------
    LinOp
        A LinOp representing the sum of the operators.
    """
    return lo.LinOp(lo.SUM, operators[0].size, operators, None)

def neg_expr(operator):
    """Negate an operator.

    Parameters
    ----------
    expr : LinOp
        The operator to be negated.

    Returns
    -------
    LinOp
        The negated operator.
    """
    return lo.LinOp(lo.NEG, operator.size, [operator], None)

def sub_expr(lh_op, rh_op):
    """Difference of linear operators.

    Parameters
    ----------
    lh_op : LinOp
        The left-hand operator in the difference.
    rh_op : LinOp
        The right-hand operator in the difference.

    Returns
    -------
    LinOp
        A LinOp representing the difference of the operators.
    """
    return sum_expr([lh_op, neg_expr(rh_op)])

def mul_expr(lh_op, rh_op, size):
    """Multiply two linear operators.

    Parameters
    ----------
    lh_op : LinOp
        The left-hand operator in the product.
    rh_op : LinOp
        The right-hand operator in the product.
    size : tuple
        The size of the product.

    Returns
    -------
    LinOp
        A linear operator representing the product.
    """
    return lo.LinOp(lo.MUL, size, [lh_op, rh_op], None)

def promote(operator, size):
    """Promotes a scalar operator to the given size.

    Parameters
    ----------
    operator : LinOp
        The operator to promote.
    size : tuple
        The dimensions to promote to.

    Returns
    -------
    LinOp
        The promoted operator.
    """
    ones = create_const(np.ones(size), size)
    return mul_expr(ones, operator, size)

def sum_entries(operator):
    """Sum the entries of an operator.

    Parameters
    ----------
    expr : LinOp
        The operator to sum the entries of.

    Returns
    -------
    LinOp
        An operator representing the sum.
    """
    return lo.LinOp(lo.SUM_ENTRIES, (1, 1), [operator], None)

def index(operator, size, keys):
    """Indexes/slices an operator.

    Parameters
    ----------
    operator : LinOp
        The expression to index.
    keys : tuple
        (row slice, column slice)
    size : tuple
        The size of the expression after indexing.

    Returns
    -------
    LinOp
        An operator representing the indexing.
    """
    return lo.LinOp(lo.INDEX, size, [operator], keys)

def transpose(operator):
    """Transposes an operator.

    Parameters
    ----------
    operator : LinOp
        The operator to transpose.

    Returns
    -------
    tuple
       (LinOp representing the transpose, [constraints])
    """
    size = (operator.size[1], operator.size[0])
    # If operator is a Variable, no need to create a new variable.
    if operator.type is lo.VARIABLE:
        return (lo.LinOp(lo.TRANSPOSE, size, [operator], None), [])
    # Operator is not a variable, create a constraint and new variable.
    else:
        new_var = create_var(operator.size)
        new_op = lo.LinOp(lo.TRANSPOSE, size, [new_var], None)
        constraints = [create_eq(new_var, operator)]
        return (new_op, constraints)

def get_constr_expr(lh_op, rh_op):
    """Returns the operator in the constraint.
    """
    # rh_op defaults to 0.
    if rh_op is None:
        return lh_op
    else:
        return sum_expr([lh_op, neg_expr(rh_op)])

def create_eq(lh_op, rh_op=None, constr_id=None):
    """Creates an internal equality constraint.

    Parameters
    ----------
    lh_term : LinOp
        The left-hand operator in the equality constraint.
    rh_term : LinOp
        The right-hand operator in the equality constraint.
    constr_id : int
        The id of the CVXPY equality constraint creating the constraint.

    Returns
    -------
    LinEqConstr
    """
    if constr_id is None:
        constr_id = get_id()
    expr = get_constr_expr(lh_op, rh_op)
    return LinEqConstr(expr, constr_id, lh_op.size)

def create_leq(lh_op, rh_op=None, constr_id=None):
    """Creates an internal less than or equal constraint.

    Parameters
    ----------
    lh_term : LinOp
        The left-hand operator in the <= constraint.
    rh_term : LinOp
        The right-hand operator in the <= constraint.
    constr_id : int
        The id of the CVXPY equality constraint creating the constraint.

    Returns
    -------
    LinLeqConstr
    """
    if constr_id is None:
        constr_id = get_id()
    expr = get_constr_expr(lh_op, rh_op)
    return LinLeqConstr(expr, constr_id, lh_op.size)

def create_geq(lh_op, rh_op=None, constr_id=None):
    """Creates an internal greater than or equal constraint.

    Parameters
    ----------
    lh_term : LinOp
        The left-hand operator in the <= constraint.
    rh_term : LinOp
        The right-hand operator in the <= constraint.
    constr_id : int
        The id of the CVXPY equality constraint creating the constraint.

    Returns
    -------
    LinLeqConstr
    """
    if rh_op is not None:
        rh_op = neg_expr(rh_op)
    return create_leq(neg_expr(lh_op), rh_op)

def get_expr_vars(operator):
    """Get a list of the variables in the operator and their sizes.

    Parameters
    ----------
    operator : LinOp
        The operator to extract the variables from.

    Returns
    -------
    list
        A list of (var id, var size) pairs.
    """
    if operator.type is lo.VARIABLE:
        return [(operator.data, operator.size)]
    else:
        vars_ = []
        for arg in operator.args:
            vars_ += get_expr_vars(arg)
        return vars_
