from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox , QHeaderView
                             , QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from Simplex import simplex, twoPhase
from Simplex import simplex
import numpy as np
import sys

class SimplexGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LP Solver")
        self.setMinimumSize(900, 700)
        self.setWindowIcon(QIcon("LP.png"))
        self.initUI()
    # Add this helper function inside class SimplexGUI (anywhere before solve_lp)

    def format_number(self, value):
        if abs(value) < 1e-9:
            value = 0
    
        if float(value).is_integer():
            return str(int(value))
            
        return f"{value:.4f}".rstrip("0").rstrip(".")

    def initUI(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Setup Row
        setup_layout = QHBoxLayout()
        self.var_input = QSpinBox()
        self.var_input.setValue(2)
        self.var_label = QLabel("Variables ->")
        self.var_label.setStyleSheet("font-weight: bold;"\
        "color: DarkRed;" \
        "font-size: 16px;" \
        "margin-left: 20px;")
        self.var_input.setMinimum(1)
        self.cons_input = QSpinBox()
        self.cons_input.setValue(3)
        self.cons_input.setMinimum(1)
        self.cons_label = QLabel("Constraints ->")
        self.cons_label.setStyleSheet("font-weight: bold;"\
        "color: DarkRed;" \
        "font-size: 16px;" \
        "margin-left: 20px;")
        setup_layout.addWidget(self.var_label)
        setup_layout.addWidget(self.var_input)
        setup_layout.addWidget(self.cons_label)
        setup_layout.addWidget(self.cons_input)

        self.Min_or_max = QComboBox()
        self.Min_or_max.addItems(["Max", "Min"])
        self.Min_or_max.setStyleSheet("background-color: DarkRed; color: Black; font-weight: bold;" \
        "font-size: 14px; height: 30px; margin-left: 20px;")
        setup_layout.addWidget(self.Min_or_max) 

        #########################################################
        #########################################################
        # YA MRAKBY -> Use Here self.Min_or_max.currentText() to determine if it's a max or min problem and adjust the objective function accordingly in solve_lp method
        #########################################################
        #########################################################

        #write to txt and the gui



        btn_gen = QPushButton("Generate Table")
        btn_gen.setStyleSheet("background-color: DarkRed ; color: Black; font-size: 14px; font-weight: bold; margin-left: 20px; height : 30px ;" )
        btn_gen.clicked.connect(self.generate_table)
        setup_layout.addWidget(btn_gen)
        layout.addLayout(setup_layout)


        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)

        # Unrestricted checkboxes
        self.unres_layout = QHBoxLayout()
        layout.addLayout(self.unres_layout)
        self.unres_checkboxes = []

        # Solve Button
        self.btn_solve = QPushButton("Solve LP")
        self.btn_solve.setStyleSheet("background-color: DarkRed; color: Black; height: 40px; font-weight: bold; font-size: 20px; margin-top: 10px;")
        self.btn_solve.clicked.connect(self.solve_lp)
        layout.addWidget(self.btn_solve)

        # Output Area
        self.output_area = QTextEdit()
        self.output_area.setStyleSheet("background-color: LightYellow; color: DarkBlue; font-size: 14px;" \
        "font-family: Consolas; margin-top: 20px;" \
        "border: 2px solid DarkRed; border-radius: 5px; padding: 10px;")
        self.output_area.setReadOnly(True)
        layout.addWidget(self.output_area)

        self.setCentralWidget(central_widget)

    def log(self, text):
        # strip HTML tags for file
        clean = text.replace("<b>", "").replace("</b>", "")
        self.output_area.append(text)  # GUI (with HTML)
        self.log_file.write(clean + "\n")  # file (plain text)

    def generate_table(self):
        # Clear previous table and checkboxes
        self.table_widget.clear()
        try:
            n_vars = self.var_input.value()
            n_cons = self.cons_input.value()
        except: return

        self.table_widget.setColumnCount(n_vars + 2)
        self.table_widget.setRowCount(n_cons + 1)
        self.table_widget.setStyleSheet("QTableWidget { border: 2px solid DarkRed; font-size: 14px; }" \
        "QHeaderView::section { background-color: DarkRed; color: Black; font-weight: bold; font-size: 14px; }" \
        "QTableWidget::item { padding: 5px; }")
        
        headers = [f"x{i+1}" for i in range(n_vars)] + ["Type"] + ["RHS"]
        self.table_widget.setHorizontalHeaderLabels(headers)
        self.table_widget.setVerticalHeaderLabels([f"Cons{i+1}" for i in range(n_cons)] + ["OBJ"])

        # Add ComboBoxes for constraint types in each row except OBJ 
        for i in range(n_cons):
            combo = QComboBox()
            combo.setStyleSheet("background-color: Darkred; color: Black; font-weight: bold;" \
            "font-size: 14px; height: 30px;")
            combo.addItems(["<=", ">=", "="])
            self.table_widget.setCellWidget(i, n_vars, combo)

        # Reset Unrestricted options 
        for cb in self.unres_checkboxes:
            self.unres_layout.removeWidget(cb)
            cb.deleteLater()
        self.unres_checkboxes = []

        for i in range(n_vars):
            cb = QCheckBox(f"X{i+1} Unrestricted")
            cb.setStyleSheet("color: DarkRed; font-weight: bold; font-size: 14px; margin-right: 10px;")
            self.unres_checkboxes.append(cb)
            self.unres_layout.addWidget(cb)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            current = self.table_widget.currentIndex()
            n_vars = self.var_input.value()
            row = current.row()
            col = current.column()

            # skip the "Type" column (n_vars)
            next_col = col + 1
            if next_col == n_vars:  # skip Type column
                next_col += 1

            if next_col > n_vars + 1:  # past RHS, go to next row
                next_col = 0
                row += 1

            if row < self.table_widget.rowCount():
                self.table_widget.setCurrentCell(row, next_col)
                self.table_widget.editItem(self.table_widget.item(row, next_col))
        else:
            super().keyPressEvent(event)

    def safe_get_item(self, r, c):
        item = self.table_widget.item(r, c)
        if item is None or item.text().strip() == "":
            return 0.0
        try:
            return float(item.text())
        except ValueError:
            return 0.0

    def solve_lp(self):
        try:
            self.log_file = open("output.txt", "w")  # clears file on each new solve
            n_vars = self.var_input.value()
            n_cons = self.cons_input.value()
            sense = self.Min_or_max.currentText()  # "Max" or "Min"

            # 1. Read constraint types
            types = []
            for i in range(n_cons):
                combo = self.table_widget.cellWidget(i, n_vars)
                if isinstance(combo, QComboBox):
                    types.append(combo.currentText())
                else:
                    types.append("<=")

            is_standard = all(t == "<=" for t in types)

            # 2. Read raw objective and constraints
            obj_raw = [self.safe_get_item(n_cons, j) for j in range(n_vars)]
            constraints_raw = []
            rhs = []
            for i in range(n_cons):
                constraints_raw.append([self.safe_get_item(i, j) for j in range(n_vars)])
                rhs.append(self.safe_get_item(i, n_vars + 1))

            obj_raw_np = np.array(obj_raw, dtype=float)
            constraints_raw_np = np.array(constraints_raw, dtype=float)
            rhs_np = np.array(rhs, dtype=float)
            unrestricted = [cb.isChecked() for cb in self.unres_checkboxes]

            if not is_standard:
                # twoPhase handles free variables, slacks, surplus, artificials internally
                x_res, opt_val, status, tables = twoPhase(
                    obj_raw_np,
                    constraints_raw_np,
                    rhs_np,
                    types,
                    n_vars,
                    n_cons,
                    unrestricted,
                    sense
                )

            else:
                # Standard simplex — handle free variables and slacks here
                new_obj = []
                new_cons = [[] for _ in range(n_cons)]
                for j in range(n_vars):
                    if unrestricted[j]:
                        new_obj.extend([obj_raw[j], -obj_raw[j]])
                        for i in range(n_cons):
                            new_cons[i].extend([constraints_raw[i][j], -constraints_raw[i][j]])
                    else:
                        new_obj.append(obj_raw[j])
                        for i in range(n_cons):
                            new_cons[i].append(constraints_raw[i][j])

                final_obj = np.array(new_obj, dtype=float)
                final_cons = np.array(new_cons, dtype=float)
                total_actual_vars = final_cons.shape[1]

                # Add slack variables
                final_cons = np.hstack((final_cons, np.eye(n_cons)))
                final_obj = np.append(final_obj, np.zeros(n_cons))

                x_res, opt_val, status, tables = simplex(
                    final_obj, final_cons, rhs_np,
                    total_actual_vars, n_cons, sense
                )

            # 3. Display results
            self.output_area.clear()
            method = "Standard Simplex" if is_standard else "Two-Phase Simplex"
            self.log(f"<b>Method:</b> {method}")
            self.log(f"<b>Problem Status:</b> {status}")

            if status == "optimal":
                self.log(f"<b>Optimal Objective Value:</b> {self.format_number(opt_val)}")
                if x_res is not None:
                    if is_standard:
                        # Standard simplex returns split vars — reconstruct
                        final_x = []
                        idx = 0
                        for j in range(n_vars):
                            if unrestricted[j]:
                                final_x.append(x_res[idx] - x_res[idx + 1])
                                idx += 2
                            else:
                                final_x.append(x_res[idx])
                                idx += 1
                    else:
                        # twoPhase already reconstructed original vars
                        final_x = list(x_res)

                    for i, val in enumerate(final_x):
                        self.log(f"Variable x{i + 1}: {self.format_number(val)}")

            self.log("\n" + "-" * 50 + "\n")
            self.log("\n<b>--- Iteration Tables ---</b>")
            for i, t in enumerate(tables):
                self.log(f"Tableau {i}:")
                for row in t:
                    formatted_row = [self.format_number(x) for x in row]
                    self.log("[" + "  ".join(formatted_row) + "]")
                self.log("\n" + "-" * 50 + "\n")
            self.log_file.close()

        except Exception as e:
            self.output_area.setText(f"{str(e)}")
            if hasattr(self, 'log_file') and not self.log_file.closed:
                self.log_file.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimplexGUI()
    window.show()
    sys.exit(app.exec())
