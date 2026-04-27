import numpy as np


def simplex(obj_function , constrains , rhs , no_of_decision_vars , no_of_constrains):
    tables = []
    table = np.zeros((no_of_constrains + 1 , constrains.shape[1] + 1) , dtype = float)
    table[:no_of_constrains , :constrains.shape[1]] = constrains
    table[:no_of_constrains , -1] = rhs
    table[-1 , :constrains.shape[1]] = obj_function * -1

    while True:

        tables.append(table.copy())

        if np.all(table[-1 , :-1] >= 0):
            break

        entering_var = np.argmin(table[-1 ,  : -1])
        ratios = np.full(no_of_constrains ,np.inf)

        for i in range(no_of_constrains):
            if table[i , entering_var] > 0:
                ratios[i] = table[i , -1] / table[i , entering_var]

        if np.all(ratios == np.inf):
            raise ValueError("unbounded")
        
        leaving_var = np.argmin(ratios)
        pivot = table[leaving_var , entering_var]

        # GAUSS_JORDON
        table[leaving_var , : ] /= pivot 
        for i in range(no_of_constrains + 1) :
            if(i != leaving_var):
                factor = table[i , entering_var]
                table[i , : ] -= factor * table[leaving_var , : ]

    optimal_value = table[-1 , -1]


    if(np.all(table[-1 , :-1] >= 0)):
        status = "optimal"
    else:
        status = "infeasible"

    return optimal_value , status , tables


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


# by Claude to debug simplex tables
def print_simplex_table(table, iteration=None, title="Simplex Tableau"):
    """
    Pretty debug print for a simplex tableau.
    Does NOT modify anything.
    """

    if iteration is not None:
        print(f"\n========== {title} (Iteration {iteration}) ==========")
    else:
        print(f"\n========== {title} ==========")

    print("\nFull Tableau:")
    print(table)

    print("\nConstraint Coefficients:")
    print(table[:-1, :-1])

    print("\nRHS (b vector):")
    print(table[:-1, -1])

    print("\nObjective Row (Reduced Costs):")
    print(table[-1, :-1])

    print("\nObjective Value (Z):")
    print(table[-1, -1])

    print("=================================================\n")




no_of_decision_vars = int(input("Enter Number Of Decision Variables: "))
no_of_constrains = int(input("Enter Number Of constrains: "))

obj_function = []
unrestricted = []
constrains = []
rhs = []
constrain_type = []

n = no_of_decision_vars

for i in range(n) :
    x = input(f"Decision Variable {i + 1} :")
    unrestricted_in = input("Is it unrestricted ( Y / N ): ")
    obj_function.append(x)
    if(unrestricted_in == "Y" or unrestricted_in == "y"):
        unrestricted.append(True)
    elif(unrestricted_in == "N" or unrestricted_in == "n"):
        unrestricted.append(False)

obj_function = np.array(obj_function , dtype = int)
unrestricted = np.array(unrestricted)

for i in range(no_of_constrains):
    for j in range(no_of_decision_vars):
        x = input(f"Coefficient of Decision Variable {j + 1} in Constrain {i + 1} :")
        constrains.append(int(x))

    constrain_type_input = input(f"Type of Constrain {i + 1} ( <= , >= , = ): ")
    if(constrain_type_input == "<="):
        constrain_type.append("<=")
    elif(constrain_type_input == ">="):
        constrain_type.append(">=")
    elif(constrain_type_input == "="):
        constrain_type.append("=")

    rhs_value = input(f"RHS of Constrain {i + 1} :")
    rhs.append(rhs_value)


constrains = np.array(constrains).reshape(no_of_constrains, no_of_decision_vars)
rhs = np.array(rhs , dtype = int)
constrain_type = np.array(constrain_type)

new_obj_function = []
new_constrains = []



for j in range(no_of_constrains):
    new_constrains.append([])

for i in range(no_of_decision_vars):
    if unrestricted[i]:
        new_obj_function.append(obj_function[i])
        new_obj_function.append(-obj_function[i])

        for j in range(no_of_constrains):
            new_constrains[j].append(constrains[j][i])
            new_constrains[j].append(-constrains[j][i])
    else :
        new_obj_function.append(obj_function[i])
        for j in range(no_of_constrains):
           new_constrains[j].append(constrains[j][i]) 

obj_function = np.array(new_obj_function)
constrains = np.array(new_constrains)

num_constraints = no_of_constrains
num_vars = constrains.shape[1]

slack_vars = 0
surplus_vars = 0

for i in range(num_constraints):
    col = np.zeros((num_constraints, 1), dtype=int)

    if constrain_type[i] == "<=":
        #Slack
        col[i, 0] = 1
        constrains = np.hstack((constrains, col))
        obj_function = np.append(obj_function, 0)
        slack_vars += 1

    elif constrain_type[i] == ">=":
        #Surplus
        col[i, 0] = -1
        constrains = np.hstack((constrains, col))
        obj_function = np.append(obj_function, 0)
        surplus_vars += 1

    elif constrain_type[i] == "=":
        continue


if np.all(constrain_type == "<="):
    opt_val, status, tables = simplex(obj_function, constrains,rhs, no_of_decision_vars , no_of_constrains)
    final_table = tables[-1]
    x = extract_basic_variables(final_table, no_of_decision_vars)

    for i, table in enumerate(tables, start=1):
        print_simplex_table(table, iteration=i)
    assert status == "optimal"

    print("Optimal decision variables:", x)
    print("Optimal objective value:", opt_val)

else :
    print("Infeasible or unbounded solution.")


