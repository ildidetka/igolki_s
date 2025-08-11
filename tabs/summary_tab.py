import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
)
import datetime

class SummaryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Контейнер для общих итогов
        totals_widget = QWidget()
        totals_layout = QHBoxLayout(totals_widget)

        # Общие итоги
        self.total_income_label = QLabel("0")
        self.total_expense_label = QLabel("0")
        self.total_net_income_label = QLabel("0")
        self.total_margin_label = QLabel("0%")
        self.avg_net_income_label = QLabel("0")  # Новая метка для среднего чистого дохода

        # Создаем виджеты с названиями и значениями
        expense_container = QVBoxLayout()
        expense_container.addWidget(QLabel("Общие траты"))
        expense_container.addWidget(self.total_expense_label)

        income_container = QVBoxLayout()
        income_container.addWidget(QLabel("Общий доход"))
        income_container.addWidget(self.total_income_label)

        net_income_container = QVBoxLayout()
        net_income_container.addWidget(QLabel("Чистый доход"))
        net_income_container.addWidget(self.total_net_income_label)

        margin_container = QVBoxLayout()
        margin_container.addWidget(QLabel("Средняя маржинальность"))
        margin_container.addWidget(self.total_margin_label)

        avg_net_container = QVBoxLayout()  # Новый контейнер для среднего чистого дохода
        avg_net_container.addWidget(QLabel("Средний чистый доход"))
        avg_net_container.addWidget(self.avg_net_income_label)

        totals_layout.addLayout(income_container)
        totals_layout.addLayout(expense_container)
        totals_layout.addLayout(net_income_container)
        totals_layout.addLayout(margin_container)
        totals_layout.addLayout(avg_net_container)  # Добавляем новый контейнер

        layout.addWidget(totals_widget)

        # Создаем виджет с шапкой колонок
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_widget.setStyleSheet("""
            background-color: #CCCCCC;
            border-radius: 5px;
            padding: 5px;
            text-align: center;
            qproperty-alignment: AlignCenter;
        """)

        header_month = QLabel("Месяц")
        header_income = QLabel("Доход")
        header_expense = QLabel("Траты")
        header_net = QLabel("Чистый доход")
        header_margin = QLabel("Маржинальность")  # Добавлен заголовок для маржинальности
        header_change = QLabel("Изменение")
        header_medianchange = QLabel("Изменение ср. дохода")


        header_layout.addWidget(header_month)
        header_layout.addWidget(header_income)
        header_layout.addWidget(header_expense)
        header_layout.addWidget(header_net)
        header_layout.addWidget(header_margin)  # Добавлен в layout
        header_layout.addWidget(header_change)
        header_layout.addWidget(header_medianchange)

        # Устанавливаем одинаковую ширину для всех колонок
        header_month.setFixedWidth(120)
        header_income.setFixedWidth(120)
        header_expense.setFixedWidth(120)
        header_net.setFixedWidth(140)
        header_margin.setFixedWidth(160)  # Установлена ширина
        header_change.setFixedWidth(120)
        header_medianchange.setFixedWidth(210)

        layout.addWidget(header_widget)

        # Создаем scrollable область для месячных данных
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.monthly_layout = QVBoxLayout(scroll_widget)
        self.monthly_layout.setSpacing(5)
        scroll_widget.setStyleSheet("""
            background-color: #ffffff;
            border-radius: 10px;
        """)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        layout.addWidget(scroll_area)

        self.setLayout(layout)
        self.update_summary()

    def format_month(self, month_str):
        months = {
            '01': 'Январь', '02': 'Февраль', '03': 'Март',
            '04': 'Апрель', '05': 'Май', '06': 'Июнь',
            '07': 'Июль', '08': 'Август', '09': 'Сентябрь',
            '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
        }
        year, month = month_str.split('-')
        return f"{months[month]} {year}"

    def update_summary(self):
        total_income = self.get_total_from_db('incomes.db')
        total_expense = self.get_total_from_db('expenses.db')
        total_net_income = total_income - total_expense

        # Рассчитываем общую маржинальность
        total_margin = (total_net_income / total_income * 100) if total_income != 0 else 0

        # Получаем месячные данные для расчета среднего
        monthly_data = self.get_monthly_data()
        monthly_nets = [month_data['income'] - month_data['expense']
                        for month_data in monthly_data.values()]
        avg_net_income = sum(monthly_nets) / len(monthly_nets) if monthly_nets else 0

        # Обновляем метки общих итогов
        self.total_income_label.setText(f"{total_income:,}")
        self.total_expense_label.setText(f"{total_expense:,}")
        self.total_net_income_label.setText(f"{total_net_income:,}")
        self.total_margin_label.setText(f"{total_margin:.2f}%")
        self.avg_net_income_label.setText(f"{avg_net_income:,.2f}")  # Форматируем с 2 знаками после запятой

        # Цветовое оформление
        self.total_income_label.setStyleSheet("color: #00CC00; font-weight: bold;")
        self.total_expense_label.setStyleSheet("color: #FF3300; font-weight: bold;")
        self.total_net_income_label.setStyleSheet("color: #3333FF; font-weight: bold;")
        self.total_margin_label.setStyleSheet("color: #FF00FF; font-weight: bold;")
        self.avg_net_income_label.setStyleSheet("color: #663399; font-weight: bold;")  # Фиолетовый цвет

        # Очищаем предыдущие месячные данные
        for i in reversed(range(self.monthly_layout.count())):
            self.monthly_layout.itemAt(i).widget().setParent(None)

        # Получаем месячные данные
        monthly_data = self.get_monthly_data()

        # Сортируем месяцы в хронологическом порядке
        sorted_months = sorted(monthly_data.keys(), key=lambda x: datetime.datetime.strptime(x, "%Y-%m"))

        # Добавляем месячные данные
        previous_net_income = None
        previous_nets = []

        for month in sorted_months:
            month_income = monthly_data[month]['income']
            month_expense = monthly_data[month]['expense']
            month_net_income = month_income - month_expense
            month_margin = (month_net_income / month_income * 100) if month_income != 0 else 0

            month_widget = QWidget()
            month_layout = QHBoxLayout(month_widget)
            month_widget.setFixedHeight(50)

            formatted_month = self.format_month(month)
            month_label = QLabel(formatted_month)
            income_label = QLabel(f"{month_income:,}")
            expense_label = QLabel(f"{month_expense:,}")
            net_label = QLabel(f"{month_net_income:,}")
            margin_label = QLabel(f"{month_margin:.2f}%")

            income_label.setStyleSheet("color: #00CC00;")
            expense_label.setStyleSheet("color: #FF3300;")
            net_label.setStyleSheet("color: #3333FF;")
            margin_label.setStyleSheet("color: #FF00FF;")

            month_label.setFixedWidth(120)
            income_label.setFixedWidth(100)
            expense_label.setFixedWidth(100)
            net_label.setFixedWidth(100)
            margin_label.setFixedWidth(100)

            # Существующая метка изменения
            change_label = QLabel()
            change_label.setFixedWidth(100)
            if previous_net_income is not None and previous_net_income != 0:
                change_percent = ((month_net_income - previous_net_income) / previous_net_income) * 100
                change_text = f"{'▲' if change_percent > 0 else '▼'} {abs(change_percent):.2f}%"
                change_label.setText(change_text)
                change_label.setStyleSheet(
                    "color: #00CC00; font-size: 16px;" if change_percent > 0 else "color: #FF3300; font-size: 16px;"
                )
            else:
                change_label.setText("0.00%")
                change_label.setStyleSheet("color: #3333FF; font-size: 16px;")


            # Новая метка с разницей между средним чистым доходом предыдущих месяцев и текущим чистым доходом
            if previous_nets:
                avg_prev_net_income = sum(previous_nets) / len(previous_nets)
                diff_percent = ((
                                            month_net_income - avg_prev_net_income) / avg_prev_net_income) * 100 if avg_prev_net_income != 0 else 0
            else:
                diff_percent = 0

            diff_label = QLabel()
            diff_label.setFixedWidth(130)

            if diff_percent > 0:
                diff_text = f"▲ {abs(diff_percent):.2f}%"
                diff_label.setStyleSheet("color: #00CC00; font-size: 16px;")
            elif diff_percent < 0:
                diff_text = f"▼ {abs(diff_percent):.2f}%"
                diff_label.setStyleSheet("color: #FF3300; font-size: 16px;")
            else:
                diff_text = f"{abs(diff_percent):.2f}%"
                diff_label.setStyleSheet("color: #3333FF; font-size: 16px;")  # синий цвет без стрелок

            diff_label.setText(diff_text)

            month_layout.addWidget(month_label)
            month_layout.addWidget(income_label)
            month_layout.addWidget(expense_label)
            month_layout.addWidget(net_label)
            month_layout.addWidget(margin_label)
            month_layout.addWidget(change_label)
            month_layout.addWidget(diff_label)  # Добавляем новую метку
            self.monthly_layout.addWidget(month_widget)
            previous_net_income = month_net_income
            previous_nets.append(month_net_income)

    def get_total_from_db(self, db_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(Стоимость) FROM data")
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0

    def get_monthly_data(self):
        monthly_data = {}

        # Подключаемся к обеим базам данных
        income_conn = sqlite3.connect('incomes.db')
        expense_conn = sqlite3.connect('expenses.db')

        income_cursor = income_conn.cursor()
        expense_cursor = expense_conn.cursor()

        # Получаем диапазон дат из обеих баз
        min_max_query = """
            SELECT 
                MIN(Дата) as min_date, 
                MAX(Дата) as max_date 
            FROM data
        """

        # Получаем минимальную и максимальную даты из доходов
        income_cursor.execute(min_max_query)
        income_min, income_max = income_cursor.fetchone()

        # Получаем минимальную и максимальную даты из расходов
        expense_cursor.execute(min_max_query)
        expense_min, expense_max = expense_cursor.fetchone()

        # Определяем общий диапазон дат
        all_dates = []
        for date in [income_min, income_max, expense_min, expense_max]:
            if date:
                all_dates.append(datetime.datetime.strptime(date, "%Y-%m-%d"))

        if not all_dates:
            return monthly_data

        min_date = min(all_dates)
        max_date = max(all_dates)

        # Генерируем все месяцы в диапазоне
        current_date = min_date.replace(day=1)
        end_date = max_date.replace(day=1)

        while current_date <= end_date:
            month_key = current_date.strftime("%Y-%m")
            monthly_data[month_key] = {'income': 0, 'expense': 0}
            current_date = (current_date + datetime.timedelta(days=32)).replace(day=1)

        # Получаем месячные доходы
        income_cursor.execute(
            "SELECT strftime('%Y-%m', Дата) as month, SUM(Стоимость) as total_income FROM data GROUP BY month")
        income_results = income_cursor.fetchall()

        # Получаем месячные расходы
        expense_cursor.execute(
            "SELECT strftime('%Y-%m', Дата) as month, SUM(Стоимость) as total_expense FROM data GROUP BY month")
        expense_results = expense_cursor.fetchall()

        # Обновляем словарь с месячными данными
        for month, income in income_results:
            if month in monthly_data:
                monthly_data[month]['income'] = income
            else:
                monthly_data[month] = {'income': income, 'expense': 0}

        for month, expense in expense_results:
            if month in monthly_data:
                monthly_data[month]['expense'] = expense
            else:
                monthly_data[month] = {'income': 0, 'expense': expense}

        income_conn.close()
        expense_conn.close()

        return monthly_data