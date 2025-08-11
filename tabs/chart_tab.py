import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea
)
import datetime
from dateutil.relativedelta import relativedelta
import pyqtgraph as pg
from pyqtgraph import DateAxisItem
import numpy as np


class ChartTab(QWidget):

    def __init__(self):
        super().__init__()
        self.init_ui()
        pg.setConfigOption('background', 'w')  # белый фон
        pg.setConfigOption('foreground', 'k')  # черные линии/текст

    def init_ui(self):
        # Создаем основной layout
        layout = QVBoxLayout()
        self.setLayout(layout)

    def plot_data(self):
        min_allowed_date = datetime.datetime(2024, 2, 1).timestamp()
        # Удаляем все существующие виджеты из layout
        while self.layout().count():
            item = self.layout().takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Создаем новый виджет графиков
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout().addWidget(self.scroll_area)

        # Вложенный виджет с графиками
        container = QWidget()
        self.scroll_area.setWidget(container)

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.GraphicsLayoutWidget()
        container_layout.addWidget(self.plot_widget)

        # Получаем данные
        min_date, max_date = self.get_date_range()
        months = self.generate_months(min_date, max_date)

        # Конвертируем строки в datetime и затем в timestamp
        x_values = []
        month_names = []  # Будем хранить названия месяцев для подписей

        for month in months:
            # Если это строка, предположим формат 'YYYY-MM'
            if isinstance(month, str):
                # Добавим день для создания полной даты
                date_str = f"{month}-01" if len(month) <= 7 else month
                dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                x_values.append(dt.timestamp())
                # Форматируем название месяца (например, "Янв 2024")
                month_names.append(dt.strftime("%B %Y"))  # %b - сокращенное название месяца
            else:
                # Если это datetime объект
                if isinstance(month, datetime.datetime):
                    x_values.append(month.timestamp())
                    month_names.append(month.strftime("%B %Y"))
                # Если это QDateTime
                elif hasattr(month, 'toPyDateTime'):
                    dt = month.toPyDateTime()
                    x_values.append(dt.timestamp())
                    month_names.append(dt.strftime("%B %Y"))

        expenses = [-self.get_sum_from_db('expenses.db', month) for month in months]
        incomes = [self.get_sum_from_db('incomes.db', month) for month in months]
        pure_income = list(np.array(incomes) + np.array(expenses))
        pure_cumulative_income = list(np.cumsum(np.array(pure_income)))
        avg_pure_income = []
        for i in range(len(pure_income)):
            ind = i
            if i == 0:
                ind = 1
            if i > 1:
                ind = i - 1
            avg = sum(pure_income[1:i + 1]) / (ind)
            avg_pure_income.append(avg)

        # Получаем данные по источникам
        sources_data = self.get_sources_data(months)

        # Создаем кастомный класс для оси X с подписями месяцев
        class CustomAxis(DateAxisItem):
            def tickStrings(self, values, scale, spacing):
                # Преобразуем timestamp обратно в дату
                dates = [datetime.datetime.fromtimestamp(v) for v in values]
                # Форматируем даты как нам нужно
                return [date.strftime('%b %Y') for date in dates]  # Например: "Янв 2024"

        # Создаем графики с нашей кастомной осью X
        plots = []
        axis = CustomAxis(orientation='bottom')

        # График доходов
        p1 = self.plot_widget.addPlot(row=0, col=0, axisItems={'bottom': axis})
        p1.setTitle("Доходы (по месяцам)", size="10pt")
        p1.showGrid(x=True, y=True)
        curve1 = p1.plot(x_values, incomes, pen=pg.mkPen('#00CC00', width=2.5), name='Доходы', symbol='o', symbolSize=8,
                         symbolBrush='#00CC00')
        p1.setYRange(min(incomes) - 1000, max(incomes) + 1000)
        line1 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('k', width=2))
        p1.addItem(line1)
        plots.append(p1)

        # График расходов
        p2 = self.plot_widget.addPlot(row=1, col=0)
        p2.setTitle("Траты (по месяцам)", size="10pt")
        p2.showGrid(x=True, y=True)
        curve2 = p2.plot(x_values, expenses, pen=pg.mkPen('#E1306C', width=2.5), name='Траты', symbol='o', symbolSize=8,
                         symbolBrush='#E1306C')
        p2.setYRange(min(expenses) - 1000, max(expenses) + 1000)
        line2 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('k', width=2))
        p2.addItem(line2)
        plots.append(p2)

        # График чистого дохода
        p3 = self.plot_widget.addPlot(row=2, col=0)
        p3.setTitle("Чистый доход (по месяцам)", size="10pt")
        p3.showGrid(x=True, y=True)
        curve3 = p3.plot(x_values, pure_income, pen=pg.mkPen('#3366FF', width=2.5), name='Чистый доход', symbol='o',
                         symbolSize=8, symbolBrush='#3366FF')
        p3.setYRange(min(pure_income) - 1000, max(pure_income) + 1000)
        line3 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('k', width=2))
        p3.addItem(line3)
        plots.append(p3)

        # График кумулятивного дохода
        p4 = self.plot_widget.addPlot(row=3, col=0)
        p4.setTitle("Чистый кумулятивный доход", size="10pt")
        p4.showGrid(x=True, y=True)
        curve4 = p4.plot(x_values, pure_cumulative_income, pen=pg.mkPen('#3333FF', width=2.5),
                         name='Чистый кумулятивный доход', symbol='o', symbolSize=8, symbolBrush='#3333FF')
        p4.setYRange(min(pure_cumulative_income) - 1000, max(pure_cumulative_income) + 1000)
        line4 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('k', width=2))
        p4.addItem(line4)
        plots.append(p4)

        # График среднего чистого дохода
        p6 = self.plot_widget.addPlot(row=4, col=0)
        p6.setTitle("Средний чистый доход (по пред. месяцам)", size="10pt")
        p6.showGrid(x=True, y=True)
        curve6 = p6.plot(x_values, avg_pure_income, pen=pg.mkPen('#FFA500', width=2.5),
                         name='Средний чистый доход', symbol='o', symbolSize=8, symbolBrush='#FFA500')
        p6.setYRange(min(avg_pure_income) - 1000, max(avg_pure_income) + 1000)
        line6 = pg.InfiniteLine(pos=0, angle=0, pen=pg.mkPen('k', width=2))
        p6.addItem(line6)
        plots.append(p6)

        # График источников (поток клиентов)
        p7 = self.plot_widget.addPlot(row=5, col=0)
        p7.setTitle("Поток клиентов (по источникам)", size="10pt")
        p7.showGrid(x=True, y=True)
        p7.getAxis('left').setWidth(36)
        colors = ['#0077FF', '#E1306C', '#0088cc', '#32CD32', '#7B68EE']
        curves5 = []  # сюда сохраним кривые для hover

        for i, (source, data) in enumerate(sources_data.items()):
            curve = p7.plot(
                x_values, data,
                pen=pg.mkPen(colors[i % len(colors)], width=2.5),
                name=source,
                symbol='o',
                symbolSize=8,
                symbolBrush=colors[i % len(colors)]
            )
            curves5.append(curve)

        # Добавляем легенду для графика источников
        legend = p7.addLegend(offset=(10, 10), verSpacing=5)
        legend.setLabelTextSize('8pt')
        plots.append(p7)

        # Связываем графики по оси X
        for i in range(1, len(plots)):
            plots[i].setXLink(plots[0])

        # Устанавливаем минимальную дату
        for plot in plots:
            plot.setLimits(xMin=min_allowed_date)

        # Настройки взаимодействия
        for p in plots:
            p.setMouseEnabled(x=True, y=False)
            p.vb.setMouseMode(pg.ViewBox.PanMode)
            p.vb.setMenuEnabled(False)
            p.enableAutoRange(x=False, y=False)

        if x_values:
            # Добавляем 1 месяц (примерно 30 дней) в секундах с каждой стороны
            month_in_seconds = 30 * 24 * 60 * 60  # 30 дней в секундах
            min_x = min(x_values) - month_in_seconds
            max_x = max(x_values) + month_in_seconds

            # Устанавливаем диапазон для всех графиков
            plots[0].setXRange(min_x, max_x, padding=0.01)



        # Подготовка данных для подсказок
        curves = [curve1, curve2, curve3, curve4, curve6] + curves5
        labels = ["Доходы", "Траты", "Чистый доход", "Кумулятивный доход", "Средний чистый доход"] + list(
            sources_data.keys())
        data_lists = [incomes, expenses, pure_income, pure_cumulative_income, avg_pure_income] + list(
            sources_data.values())

        # Создаем список для хранения подсказок
        self.hover_points = []
        self.text_items = []

        for i, (curve, label, data) in enumerate(zip(curves, labels, data_lists)):
            # Определяем, на каком графике должна быть подсказка
            plot_idx = i if i < 5 else 5  # Источники идут на 5-м графике

            plot = plots[plot_idx]

            # Создаем точку для отслеживания
            hover_point = pg.ScatterPlotItem(pen=pg.mkPen('k', width=2), brush=pg.mkBrush('w'), size=10, symbol='o')
            hover_point.setZValue(100)
            plot.addItem(hover_point)
            self.hover_points.append(hover_point)

            # Создаем метку для отображения значения
            text_item = pg.TextItem(
                text="",
                anchor=(0, 0.5),
                color='k',
                fill=pg.mkColor(255, 255, 255, 200),
                border=pg.mkColor(0, 0, 0)
            )
            text_item.setZValue(101)
            plot.addItem(text_item)
            self.text_items.append(text_item)

        for plot in plots:
            # Настраиваем отображение подписей на оси X
            plot.getAxis('bottom').setStyle(
                tickFont=pg.Qt.QtGui.QFont("Arial", 8),
                tickLength=10,
                tickTextOffset=5
            )

            # Устанавливаем подписи для всех значений
            plot.getAxis('bottom').setTicks([[(v, month_names[i]) for i, v in enumerate(x_values)]])

        # Функция для обновления всех подсказок
        def update_cursors(event):
            pos = event[0]
            for plot in plots:
                if plot.sceneBoundingRect().contains(pos):
                    mouse_point = plot.vb.mapSceneToView(pos)
                    nearest_idx = np.argmin(np.abs(np.array(x_values) - mouse_point.x()))
                    if nearest_idx < len(x_values):
                        for i, (curve, label, data) in enumerate(zip(curves, labels, data_lists)):
                            # Получаем цвет линии графика
                            line_color = curve.opts['pen'].color()
                            bg_color = pg.mkColor(line_color)
                            bg_color.setAlpha(150)

                            # Обновляем положение точки
                            self.hover_points[i].setData([x_values[nearest_idx]], [data[nearest_idx]])

                            # Определяем положение текста
                            plot_idx = i if i < 5 else 5
                            current_plot = plots[plot_idx]

                            # Фиксированные позиции для подсказок
                            if plot_idx < 5:  # Первые 5 графиков
                                x_pos = current_plot.vb.viewRange()[0][1] - 0.1 * (
                                        current_plot.vb.viewRange()[0][1] - current_plot.vb.viewRange()[0][0])
                                y_pos = current_plot.vb.viewRange()[1][1] - 0.1 * (
                                        current_plot.vb.viewRange()[1][1] - current_plot.vb.viewRange()[1][0])
                            else:  # График источников
                                x_pos = current_plot.vb.viewRange()[0][1] - 0.1 * (
                                        current_plot.vb.viewRange()[0][1] - current_plot.vb.viewRange()[0][0])
                                y_pos = current_plot.vb.viewRange()[1][1] - (i - 5 + 1) * (
                                        current_plot.vb.viewRange()[1][1] * 0.15)

                            # Обновляем текст, позицию и цвет фона подсказки
                            value = data[nearest_idx]
                            if isinstance(value, float):
                                value = round(value, 1)
                            self.text_items[i].setText(f"{label}: {value}")
                            self.text_items[i].setPos(x_pos, y_pos)
                            self.text_items[i].fill = pg.mkBrush(bg_color)
                            self.text_items[i].setTextWidth(150)
                        return
            # Скрываем подсказки, если мышь не над графиком
            for i in range(len(curves)):
                self.hover_points[i].setData([], [])
                self.text_items[i].setText("")

        # Привязываем функцию к событию движения мыши для всех графиков
        for plot in plots:
            proxy = pg.SignalProxy(
                plot.scene().sigMouseMoved,
                rateLimit=10,
                slot=update_cursors
            )
            setattr(self, f"proxy_{plot}", proxy)

    def get_sources_data(self, months):
        sources = ["VK", "Instagram", "Telegram", "Авито", "Знакомые"]
        sources_data = {source: [] for source in sources}

        conn = sqlite3.connect('incomes.db')
        cursor = conn.cursor()

        for month in months:
            cursor.execute("SELECT Источник, COUNT(*) FROM data WHERE strftime('%Y-%m', Дата) = ? GROUP BY Источник",
                           (month,))
            results = cursor.fetchall()
            month_data = {source: 0 for source in sources}
            for source, count in results:
                if source in month_data:
                    month_data[source] = count
            for source in sources:
                sources_data[source].append(month_data[source])

        conn.close()
        return sources_data

    def get_sum_from_db(self, db_name, month):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(Стоимость) FROM data WHERE strftime('%Y-%m', Дата) = ?", (month,))
        result = cursor.fetchone()[0]
        conn.close()
        return result if result else 0

    def get_date_range(self):
        conn = sqlite3.connect('incomes.db')
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(Дата), MAX(Дата) FROM data")

        cursor.execute("ATTACH DATABASE 'expenses.db' AS db2")
        cursor.execute("SELECT MIN(Дата), MAX(Дата) FROM data")
        min_date_db1, max_date_db1 = cursor.fetchone()

        cursor.execute("SELECT MIN(Дата), MAX(Дата) FROM db2.data")
        min_date_db2, max_date_db2 = cursor.fetchone()

        min_date = min(filter(None, [min_date_db1, min_date_db2])) if any(
            [min_date_db1, min_date_db2]) else '2024-04-04'
        max_date = max(filter(None, [max_date_db1, max_date_db2])) if any(
            [max_date_db1, max_date_db2]) else '2024-06-04'

        # РАСШИРЯЕМ ДИАПАЗОН НА 1 МЕС ДЛЯ КОРРЕКТНОГО ОТОБРАЖЕНИЯ ГРАФИКОВ
        min_date_dt = datetime.datetime.strptime(min_date, '%Y-%m-%d')
        max_date_dt = datetime.datetime.strptime(max_date, '%Y-%m-%d')

        min_date_dt = min_date_dt - relativedelta(months=1)
        max_date_dt = max_date_dt + relativedelta(months=1)

        min_date = datetime.datetime.strftime(min_date_dt, '%Y-%m-%d')
        max_date = datetime.datetime.strftime(max_date_dt, '%Y-%m-%d')

        conn.close()
        return min_date, max_date

    def generate_months(self, start, end):
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
        return [(start_date + datetime.timedelta(days=i * 30)).strftime('%Y-%m') for i in
                range((end_date - start_date).days // 30 + 1)]