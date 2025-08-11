import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt
import datetime
from dateutil.relativedelta import relativedelta




class HomeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        self.header_label = QLabel()
        self.header_label.setObjectName("summaryLabel")
        self.header_label.setStyleSheet("margin: 15px auto;")
        layout.addWidget(self.header_label)
        # Карточка итогов
        self.totals_widget = QWidget()
        totals_layout = QHBoxLayout(self.totals_widget)
        self.totals_widget.setStyleSheet("""
            background-color: #fff;
            border-radius: 10px;
            padding: 10px;
            text-align: center;
        """)

        # Метки
        self.income_label = QLabel()
        self.expense_label = QLabel()
        self.net_label = QLabel()
        self.margin_label = QLabel()
        self.conversion_label = QLabel()
        self.orders_label = QLabel()
        self.change_label = QLabel()
        self.avg_diff_label = QLabel()

        def create_card(title, label, color):
            container = QVBoxLayout()
            title_lbl = QLabel(title)
            title_lbl.setStyleSheet("font-size: 14px;")
            label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")
            container.addWidget(title_lbl)
            container.addWidget(label)
            return container


        totals_layout.addLayout(create_card("Доход", self.income_label, "#00CC00"))
        totals_layout.addLayout(create_card("Расход", self.expense_label, "#FF3300"))
        totals_layout.addLayout(create_card("Чистый доход", self.net_label, "#3333FF"))
        totals_layout.addLayout(create_card("Маржинальность", self.margin_label, "#FF00FF"))
        totals_layout.addLayout(create_card("Конверсия", self.conversion_label, "#000000"))
        totals_layout.addLayout(create_card("Кол-во клиентов", self.orders_label, "#0077FF"))
        totals_layout.addLayout(create_card("Изменение дохода от пред. месяца", self.change_label, "#3333FF"))
        totals_layout.addLayout(create_card("Отклонение чистого дохода от среднего дохода", self.avg_diff_label, "#663399"))

        layout.addWidget(self.totals_widget)

        self.update_data()

    def update_data(self):
        now = datetime.datetime.now()
        this_month = now.strftime("%Y-%m")
        prev_month = (now - relativedelta(months=1)).strftime("%Y-%m")

        month_names = {
            '01': 'Январь', '02': 'Февраль', '03': 'Март',
            '04': 'Апрель', '05': 'Май', '06': 'Июнь',
            '07': 'Июль', '08': 'Август', '09': 'Сентябрь',
            '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
        }

        month_str = now.strftime('%m')
        year_str = now.strftime('%Y')
        self.header_label.setText(f"Данные за {month_names[month_str]} {year_str}")

        def get_total(db_name, month):
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(Стоимость) FROM data WHERE strftime('%Y-%m', Дата) = ?", (month,))
            result = cursor.fetchone()[0]
            conn.close()
            return result or 0

        def get_count(db_name, month):
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM data WHERE strftime('%Y-%m', Дата) = ?", (month,))
            result = cursor.fetchone()[0]
            conn.close()
            return result

        def get_conversion(month):
            leads_conn = sqlite3.connect('leads.db')
            sales_conn = sqlite3.connect('incomes.db')
            lc = leads_conn.cursor()
            sc = sales_conn.cursor()
            lc.execute("SELECT COUNT(*) FROM data WHERE strftime('%Y-%m', Дата) = ?", (month,))
            sc.execute("SELECT COUNT(*) FROM data WHERE strftime('%Y-%m', Дата) = ?", (month,))
            leads = lc.fetchone()[0]
            sales = sc.fetchone()[0]
            leads_conn.close()
            sales_conn.close()
            return round((sales / leads) * 100, 2) if leads > 0 else 0



        income = get_total('incomes.db', this_month)
        expense = get_total('expenses.db', this_month)
        net = income - expense
        margin = round((net / income) * 100, 2) if income > 0 else 0
        orders = get_count('incomes.db', this_month)
        conv = get_conversion(this_month)

        prev_net = get_total('incomes.db', prev_month) - get_total('expenses.db', prev_month)
        net_diff = net - prev_net
        net_percent = (net_diff / abs(prev_net) * 100) if prev_net != 0 else 0

        # Обновляем значения
        self.income_label.setText(f"{income:,}")
        self.expense_label.setText(f"{expense:,}")
        self.net_label.setText(f"{net:,}")
        self.margin_label.setText(f"{margin:.2f}%")
        self.conversion_label.setText(f"{conv:.2f}%")
        self.orders_label.setText(f"{orders}")
        if prev_net != 0:
            arrow = '▲' if net_diff > 0 else '▼'
            color = "#00CC00" if net_diff > 0 else "#FF3300"
            self.change_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 18px;")
            self.change_label.setText(f"{arrow} {abs(net_percent):.2f}%")
        else:
            self.change_label.setText("Нет данных")

        def get_all_months_net():
            conn_income = sqlite3.connect('incomes.db')
            conn_exp = sqlite3.connect('expenses.db')
            cur_income = conn_income.cursor()
            cur_exp = conn_exp.cursor()

            cur_income.execute(
                "SELECT strftime('%Y-%m', Дата), SUM(Стоимость) FROM data GROUP BY strftime('%Y-%m', Дата)")
            income_by_month = dict(cur_income.fetchall())

            cur_exp.execute("SELECT strftime('%Y-%m', Дата), SUM(Стоимость) FROM data GROUP BY strftime('%Y-%m', Дата)")
            expense_by_month = dict(cur_exp.fetchall())

            conn_income.close()
            conn_exp.close()

            all_months = set(income_by_month.keys()).union(expense_by_month.keys())
            net_values = []
            current_month = datetime.datetime.now().strftime("%Y-%m")

            for month in all_months:
                if month == current_month:  # Пропускаем текущий месяц
                    continue
                inc = income_by_month.get(month, 0)
                exp = expense_by_month.get(month, 0)
                net_values.append(inc - exp)

            return net_values

        net_all = get_all_months_net()
        avg_net = sum(net_all) / (len(net_all) + 2) if net_all else 0
        print(avg_net)
        diff_from_avg = net - avg_net
        diff_percent = (diff_from_avg / avg_net * 100) if avg_net != 0 else 0

        # Обновляем метку
        arrow_avg = '▲' if diff_from_avg > 0 else '▼'
        color_avg = "#00CC00" if diff_from_avg > 0 else "#FF3300"
        self.avg_diff_label.setStyleSheet(f"color: {color_avg}; font-weight: bold; font-size: 18px;")
        self.avg_diff_label.setText(f"{arrow_avg} {abs(diff_percent):.2f}%")