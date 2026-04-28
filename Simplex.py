import sys
import numpy as np

def simplex(obj_function , constrains , rhs , no_of_decision_vars , no_of_constrains, mode):
    tables = []
    table = np.zeros((no_of_constrains + 1 , constrains.shape[1] + 1) , dtype = float)
    table[:no_of_constrains , :constrains.shape[1]] = constrains
    table[:no_of_constrains , -1] = rhs

    if mode == "Min":
        obj_function = obj_function.copy() * -1
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
    if(mode == "Min"):
        optimal_value*=-1
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


def twoPhase(obj,constrains , rhs ,constraint_types, n_decision_vars , n_constrains,unrestricted, mode):
    new_obj= []
    new_constrains_cols = []
    artificial_indices = []
    #this for free variables
    for i in range (n_decision_vars):
        if unrestricted[i]:
            new_obj.append(obj[i])
            new_obj.append(-obj[i])
            new_constrains_cols.append(constrains[:,i])
            new_constrains_cols.append(-constrains[:, i])
        else:
            new_obj.append(obj[i])
            new_constrains_cols.append(constrains[:,i])
    new_constrains=np.column_stack(new_constrains_cols)
    new_obj=np.array(new_obj)

    #here to handle surpass,artificial, etc

    for i,type in enumerate(constraint_types):
        if type== "<=":
            slack_col=np.zeros(n_constrains)
            slack_col[i] = 1
            new_constrains=np.hstack((new_constrains,slack_col.reshape(-1,1)))
            new_obj=np.append(new_obj,0)

        elif type== ">=":
            surplus_col=np.zeros(n_constrains)
            surplus_col[i] = -1
            art_col=np.zeros(n_constrains)
            art_col[i] = 1
            new_constrains=np.hstack((new_constrains,surplus_col.reshape(-1,1)))
            new_obj=np.append(new_obj,0)
            new_constrains=np.hstack((new_constrains,art_col.reshape(-1,1)))
            new_obj=np.append(new_obj,0)

            artificial_indices.append(new_constrains.shape[1]-1)

        elif type== "=":
            art_col=np.zeros(n_constrains)
            art_col[i] = 1
            new_constrains=np.hstack((new_constrains,art_col.reshape(-1,1)))
            new_obj=np.append(new_obj,0)
            artificial_indices.append(new_constrains.shape[1]-1)

    phase1_obj=np.zeros(new_constrains.shape[1])
    phase1_obj[artificial_indices] = 1
    for idx in artificial_indices:
        col = new_constrains[:, idx]
        row = np.where(np.isclose(col, 1, atol=1e-9))[0]
        if len(row) == 1:
            phase1_obj = phase1_obj - phase1_obj[idx] * new_constrains[row[0], :]
    _, phase1_val, status, tables_p1 = simplex(phase1_obj, new_constrains, rhs, new_constrains.shape[1], n_constrains,"Min")
    if phase1_val > 1e-9: # type: ignore
        return None, None, "infeasible", tables_p1

    phase2_constrains=np.delete(new_constrains, artificial_indices, axis=1)
    phase2_obj=np.delete(new_obj, artificial_indices)
    final_p1_table= tables_p1[-1]
    p1_basis_tableau = np.delete(final_p1_table, artificial_indices , axis=1)  # remove art cols but keep RHS

    updated_rhs = final_p1_table[:n_constrains, -1]
    p1_constraint_rows = p1_basis_tableau[:n_constrains, :phase2_constrains.shape[1]]
    for j in range(phase2_constrains.shape[1]):
        col = p1_constraint_rows[:, j]
        row_indices = np.where(np.isclose(col, 1, atol=1e-9))[0]
        if len(row_indices) == 1:
            i = row_indices[0]
            if np.all(np.isclose(np.delete(col, i), 0, atol=1e-9)):
                factor = phase2_obj[j]
                if not np.isclose(factor, 0, atol=1e-9):
                    phase2_obj = phase2_obj - factor * p1_constraint_rows[i, :]

    x, opt_val, status, tables_p2 = simplex(phase2_obj, p1_constraint_rows ,updated_rhs, p1_constraint_rows.shape[1], n_constrains, mode)
    all_tables=tables_p1+tables_p2
    return x, opt_val, status, all_tables








