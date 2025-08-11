import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QMessageBox
)
from datetime import date




class PromotionTab(QWidget):
    def __init__(self):
        super().__init__()
        self.conn = sqlite3.connect('promotion.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                Дата TEXT,
                Действие TEXT
            )
        ''')
        self.conn.commit()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Дата", "Действие"])
        self.table.setColumnWidth(0, 150)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.setStyleSheet("QTableWidget { gridline-color: #808080; }")
        layout.addWidget(self.table)

        # Поля ввода
        input_layout = QHBoxLayout()
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("дд.мм.гггг")
        self.action_input = QLineEdit()
        self.action_input.setPlaceholderText("Что сделал")
        self.date_input.setText(date.today().strftime("%d.%m.%Y"))

        input_layout.addWidget(QLabel("Дата:"))
        input_layout.addWidget(self.date_input)
        input_layout.addWidget(QLabel("Действие:"))
        input_layout.addWidget(self.action_input)

        layout.addLayout(input_layout)

        # Кнопка
        add_btn = QPushButton("Добавить запись")
        add_btn.clicked.connect(self.add_record)
        layout.addWidget(add_btn)

        self.setLayout(layout)
        self.load_data()

    def load_data(self):
        self.table.setRowCount(0)
        self.cursor.execute("SELECT Дата, Действие FROM data ORDER BY Дата ASC")
        for i, row in enumerate(self.cursor.fetchall()):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))

    def add_record(self):
        date_str = self.date_input.text().strip()
        action = self.action_input.text().strip()

        if not date_str or not action:
            QMessageBox.warning(self, "Ошибка", "Заполните оба поля.")
            return

        try:
            # проверка и формат даты
            d, m, y = date_str.split(".")
            iso_date = f"{y}-{m}-{d}"
        except:
            QMessageBox.warning(self, "Ошибка", "Неверный формат даты.")
            return

        self.cursor.execute("INSERT INTO data (Дата, Действие) VALUES (?, ?)", (iso_date, action))
        self.conn.commit()
        self.load_data()
        self.action_input.clear()