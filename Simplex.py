import sys
import numpy as np

def simplex(obj_function , constrains , rhs , no_of_decision_vars , no_of_constrains):
    tables = []
    table = np.zeros((no_of_constrains + 1 , constrains.shape[1] + 1) , dtype = float)
    table[:no_of_constrains , :constrains.shape[1]] = constrains
    table[:no_of_constrains , -1] = rhs
    table[-1 , :constrains.shape[1]] = obj_function * -1

    while True:

        tables.append(table.copy())

        if np.all(table[-1 , :-1] >= -1e-9):
            break

        entering_var = np.argmin(table[-1 ,  : -1])
        ratios = np.full(no_of_constrains ,np.inf)

        for i in range(no_of_constrains):
            if table[i , entering_var] > 0:
                ratios[i] = table[i , -1] / table[i , entering_var]

        if np.all(ratios == np.inf):
            return None , None , "unbounded" , tables
        
        leaving_var = np.argmin(ratios)
        pivot = table[leaving_var , entering_var]

        # GAUSS_JORDON
        table[leaving_var , : ] /= pivot 
        for i in range(no_of_constrains + 1) :
            if(i != leaving_var):
                factor = table[i , entering_var]
                table[i , : ] -= factor * table[leaving_var , : ]

    optimal_value = table[-1 , -1]
    status = "optimal"
    x = extract_basic_variables(table, constrains.shape[1]) # Extract from all columns
    return x, optimal_value, status, tables


def extract_basic_variables(final_table, no_of_decision_vars, tol=1e-9):

    m = final_table.shape[0] - 1  # last row is objective function
    x = np.zeros(no_of_decision_vars)

    for j in range(no_of_decision_vars):
        column = final_table[:m, j]

        if np.isclose(column.sum(), 1, atol=tol): # 0 --- 1 ---- 0 -> sum = 1
            row_indices = np.where(np.isclose(column, 1, atol=tol))[0]

            if len(row_indices) == 1 and np.all(np.isclose(np.delete(column, row_indices[0]), 0, atol=tol)):
                row = row_indices[0]
                x[j] = final_table[row, -1]

    return x