from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTableWidget, QTableWidgetItem, 
                             QPushButton, QLabel, QLineEdit, QTextEdit, QCheckBox, QComboBox , QHeaderView
                             , QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

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

    def generate_table(self):
        # Clear previous table and checkboxes
        self.table_widget.clear()
        try:
            n_vars = int(self.var_input.text())
            n_cons = int(self.cons_input.text())
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
            n_vars = int(self.var_input.text())
            n_cons = int(self.cons_input.text())
            
            # 1. Check Constraint Types to decide the method [cite: 9, 10, 13]
            types = []
            for i in range(n_cons):
                combo = self.table_widget.cellWidget(i, n_vars)
                if isinstance(combo, QComboBox):
                    types.append(combo.currentText())
                else:
                    types.append("<=") 

            is_standard = all(t == "<=" for t in types)

            if not is_standard:
                self.output_area.setText("Method: Two-Phase Simplex required.")
                return

            # 2. Proceed with Standard Simplex Logic [cite: 9]
            obj_raw = [self.safe_get_item(n_cons, j) for j in range(n_vars)]
            constraints_raw = []
            rhs = []
            for i in range(n_cons):
                constraints_raw.append([self.safe_get_item(i, j) for j in range(n_vars)])
                # RHS is now in the last column (n_vars + 1)
                rhs.append(self.safe_get_item(i, n_vars + 1))

            # Handle Unrestricted Variables [cite: 11]
            new_obj = []
            new_cons = [[] for _ in range(n_cons)]
            for j in range(n_vars):
                if self.unres_checkboxes[j].isChecked():
                    new_obj.extend([obj_raw[j], -obj_raw[j]])
                    for i in range(n_cons):
                        new_cons[i].extend([constraints_raw[i][j], -constraints_raw[i][j]])
                else:
                    new_obj.append(obj_raw[j])
                    for i in range(n_cons):
                        new_cons[i].append(constraints_raw[i][j])

            # Convert to numpy and add Slack
            final_obj = np.array(new_obj)
            final_cons = np.array(new_cons)
            total_actual_vars = final_cons.shape[1]
            
            slacks = np.eye(n_cons)
            final_cons = np.hstack((final_cons, slacks))
            final_obj = np.append(final_obj, np.zeros(n_cons))

            # Solve using your logic [cite: 7]
            # Ensure simplex is imported correctly from your file
            from Simplex import simplex 
            x_res, opt_val, status, tables = simplex(final_obj, final_cons, np.array(rhs), total_actual_vars, n_cons,self.Min_or_max)

            # Output results
            self.output_area.clear()
            self.output_area.append(f"<b>Method:</b> Standard Simplex")
            self.output_area.append(f"<b>Problem Status:</b> {status}")
            
            if status == "optimal":
                self.output_area.append(f"<b>Optimal Objective Value:</b> {self.format_number(opt_val)}")
                final_x = []
                idx = 0
                for j in range(n_vars):
                    if self.unres_checkboxes[j].isChecked():
                        if x_res is not None:
                            final_x.append(x_res[idx] - x_res[idx+1])
                            idx += 2
                    else:
                        if x_res is not None:    
                            final_x.append(x_res[idx])
                            idx += 1
                
                for i, val in enumerate(final_x):
                    self.output_area.append(f"Variable x{i+1}: {self.format_number(val)}")

            self.output_area.append("\n" + "-" * 50 + "\n")
            self.output_area.append("\n<b>--- Iteration Tables ---</b>")
            for i, t in enumerate(tables):
                self.output_area.append(f"Tableau {i}:")
                for row in t:
                    formatted_row = [self.format_number(x) for x in row]
                    self.output_area.append("[" + "  ".join(formatted_row) + "]")
                self.output_area.append("\n" + "-" * 50 + "\n")
        except Exception as e:
            self.output_area.setText(f"{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SimplexGUI()
    window.show()
    sys.exit(app.exec())
