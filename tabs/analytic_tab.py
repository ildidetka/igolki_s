import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QSpinBox
)
import datetime
from datetime import date
import pyqtgraph as pg



class AnalyticsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect('leads.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS data (
                id INTEGER PRIMARY KEY,
                Дата TEXT,
                Источник TEXT
            )
        ''')
        self.conn.commit()

    def init_ui(self):
        layout = QVBoxLayout()

        # Верхняя часть с полем ввода количества и кнопками источников
        top_layout = QHBoxLayout()

        # Поле для ввода количества лидов
        self.lead_count_input = QSpinBox()
        self.lead_count_input.setMinimum(1)
        self.lead_count_input.setMaximum(999)
        self.lead_count_input.setValue(1)
        top_layout.addWidget(QLabel("Количество лидов:"))
        top_layout.addWidget(self.lead_count_input)
        top_layout.addStretch()

        layout.addLayout(top_layout)

        # Кнопки "Добавить лид"
        self.sources = ["VK", "Instagram", "Telegram", "Авито", "Знакомые"]
        button_layout = QHBoxLayout()

        for source in self.sources:
            btn = QPushButton(f"Добавить из {source}")
            btn.clicked.connect(lambda _, s=source: self.add_lead(s))
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)

        # Таблица для показа аналитики
        self.table = QTableWidget()
        self.table.setColumnCount(1 + len(self.sources) + 3)  # +3 (конверсия, лиды, покупатели)
        self.table.setHorizontalHeaderLabels(
            ["Месяц"] + self.sources + ["Конверсия", "Итого лидов", "Итого покупателей"])
        layout.addWidget(self.table)
        self.table.setColumnWidth(0, 250)
        for i in range(1, 8):  # Теперь 8 столбцов (0-7)
            self.table.setColumnWidth(i, 150)
        self.table.setColumnWidth(8, 250)
        self.setLayout(layout)
        self.update_table()

        self.plot_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.plot_widget)
        self.plot_data()  # строим при запуске
        self.plot_data()  # строим при запуске

    def plot_data(self):
        self.plot_widget.clear()

        sources = self.sources
        months = self.get_all_months()
        x_labels = [datetime.datetime.strptime(m, "%Y-%m") for m in months]
        x_vals = [dt.timestamp() for dt in x_labels]

        leads_data = {s: [] for s in sources}
        sales_data = {s: [] for s in sources}
        total_leads = []
        total_sales = []
        conversions = {}

        for m in months:
            tl = ts = 0
            for s in sources:
                l = self.get_lead_count(m, s)
                b = self.get_buy_count(m, s)
                leads_data[s].append(l)
                sales_data[s].append(b)
                tl += l
                ts += b
            total_leads.append(tl)
            total_sales.append(ts)

        for s in sources:
            conversions[s] = [
                round((b / l) * 100, 2) if l > 0 else 0
                for b, l in zip(sales_data[s], leads_data[s])
            ]
        conversions["Итого"] = [
            round((b / l) * 100, 2) if l > 0 else 0
            for b, l in zip(total_sales, total_leads)
        ]

        # График
        plot = self.plot_widget.addPlot(title="Конверсия по источникам")
        plot.showGrid(x=True, y=True)
        plot.setLabel("left", "Конверсия, %")
        plot.setLabel("bottom", "Месяц")
        plot.setAxisItems({'bottom': pg.DateAxisItem(orientation='bottom')})

        colors = ['#0077FF', '#E1306C', '#0088cc', '#32CD32', '#7B68EE']
        for i, s in enumerate(sources):
            plot.plot(
                x_vals, conversions[s],
                pen=pg.mkPen(colors[i % len(colors)], width=2),
                name=s
            )

        plot.plot(
            x_vals, conversions["Итого"],
            pen=pg.mkPen('black', width=3),
            name="Итого"
        )

        # Создаем легенду и размещаем ее справа
        legend = plot.addLegend(offset=(10, 10))  # Отступ от правого края
        legend.setBrush(pg.mkBrush(color=(255, 255, 255, 150)))  # Полупрозрачный белый фон

        plot.addLegend(offset=(50, 10))
        plot.setXRange(min(x_vals), max(x_vals), padding=0.01)
        plot.setYRange(-30, 130)
        # Разрешаем только горизонтальную прокрутку
        plot.setMouseEnabled(x=True, y=False)
        # Отключаем масштабирование
        plot.vb.setMouseMode(pg.ViewBox.PanMode)
        # Отключаем контекстное меню
        plot.vb.setMenuEnabled(False)
        # Отключаем автомасштабирование
        plot.enableAutoRange(x=False, y=False)

    def add_lead(self, source):
        count = self.lead_count_input.value()

        if count > 1:
            confirm = QMessageBox.question(
                self, 'Добавление лидов',
                f"Вы уверены, что хотите добавить {count} лидов из {source}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            confirm = QMessageBox.question(
                self, 'Добавление лида',
                f"Вы уверены, что хотите добавить лида из {source}?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        if confirm == QMessageBox.StandardButton.Yes:
            today = date.today().strftime("%Y-%m-%d")
            self.cursor.executemany(
                "INSERT INTO data (Дата, Источник) VALUES (?, ?)",
                [(today, source)] * count
            )
            self.conn.commit()
            self.update_table()
            self.plot_data()

    def update_table(self):
        self.table.setRowCount(0)
        months = self.get_all_months()

        for i, month in enumerate(months):
            row_data = []
            total_leads = 0
            total_buys = 0

            # Данные по источникам
            for source in self.sources:
                leads = self.get_lead_count(month, source)
                buys = self.get_buy_count(month, source)
                conv = round(buys / leads * 100, 2) if leads > 0 else 0
                row_data.append(f"{buys}/{leads} ({conv:.1f}%)")
                total_leads += leads
                total_buys += buys

            # Добавляем конверсию
            total_conv = round(total_buys / total_leads * 100, 2) if total_leads > 0 else 0
            row_data.append(f"{total_conv:.1f}%")

            # Добавляем итого лидов
            row_data.append(str(total_leads))

            # Добавляем итого покупателей (новый столбец)
            row_data.append(str(total_buys))

            # Заполняем строку таблицы
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(self.format_month(month)))
            for j, val in enumerate(row_data):
                self.table.setItem(i, j + 1, QTableWidgetItem(val))

    def get_counts_from_db(self, db_name):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT strftime('%Y-%m', Дата) as month, COUNT(*) FROM data GROUP BY month")
        data = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return data

    def format_month(self, month_str):
        months = {
            '01': 'Январь', '02': 'Февраль', '03': 'Март',
            '04': 'Апрель', '05': 'Май', '06': 'Июнь',
            '07': 'Июль', '08': 'Август', '09': 'Сентябрь',
            '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
        }
        year, month = month_str.split('-')
        return f"{months[month]} {year}"

    def get_all_months(self):
        # Получаем минимальную и максимальную даты из обеих баз
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(Дата), MAX(Дата) FROM data")
        min_date1, max_date1 = cursor.fetchone()
        cursor.close()

        conn = sqlite3.connect('incomes.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(Дата), MAX(Дата) FROM data")
        min_date2, max_date2 = cursor.fetchone()
        cursor.close()

        # Определяем общий диапазон дат
        min_date = min(min_date1 or "3000-01-01", min_date2 or "3000-01-01")
        max_date = max(max_date1 or "1000-01-01", max_date2 or "1000-01-01")

        if min_date > max_date:  # Если нет данных
            return []

        # Генерируем все месяцы в диапазоне
        start = datetime.datetime.strptime(min_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(max_date, "%Y-%m-%d")

        months = []
        current = start
        while current <= end:
            months.append(current.strftime("%Y-%m"))
            # Переходим к следующему месяцу
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        return months

    def get_lead_count(self, month, source):
        conn = sqlite3.connect('leads.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM data WHERE strftime('%Y-%m', Дата) = ? AND Источник = ?", (month, source))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def get_buy_count(self, month, source):
        conn = sqlite3.connect('incomes.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM data WHERE strftime('%Y-%m', Дата) = ? AND Источник = ?", (month, source))
        count = cursor.fetchone()[0]
        conn.close()
        return count