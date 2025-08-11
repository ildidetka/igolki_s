# from PyQt6.QtWidgets import QWidget, QVBoxLayout
# from PyQt6.QtChart import QChartView, QChart, QPieSeries
# from PyQt6.QtGui import QPainter
# from PyQt6.QtCore import Qt
# import sqlite3
#
# class PieChartTab(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         layout = QVBoxLayout(self)
#
#         # Первый пайчарт — по городам
#         city_series = self.build_series("Город")
#         city_chart = QChart()
#         city_chart.addSeries(city_series)
#         city_chart.setTitle("Заказы по городам")
#         city_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
#
#         city_view = QChartView(city_chart)
#         city_view.setRenderHint(QPainter.RenderHint.Antialiasing)
#         layout.addWidget(city_view)
#
#         # Второй пайчарт — по типам вышивки
#         type_series = self.build_series("Тип вышивки")
#         type_chart = QChart()
#         type_chart.addSeries(type_series)
#         type_chart.setTitle("Типы вышивки")
#         type_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
#
#         type_view = QChartView(type_chart)
#         type_view.setRenderHint(QPainter.RenderHint.Antialiasing)
#         layout.addWidget(type_view)
#
#     def build_series(self, column_name):
#         series = QPieSeries()
#         conn = sqlite3.connect("incomes.db")
#         cursor = conn.cursor()
#         cursor.execute(f"SELECT [{column_name}], COUNT(*) FROM data GROUP BY [{column_name}]")
#         results = cursor.fetchall()
#         conn.close()
#
#         for label, count in results:
#             label = label if label else "Не указано"
#             series.append(label, count)
#         return series
#
#     def update_data(self):
#         self.__init__(self.parent())  # Просто пересоздаём вкладку (ленивый способ)
