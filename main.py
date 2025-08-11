import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget
)
from PyQt6.QtGui import QIcon
from style import style as st
import pyqtgraph as pg

from tabs.chart_tab import ChartTab
from tabs.summary_tab import SummaryTab
from tabs.widget_tab import TabWidget
from tabs.analytic_tab import AnalyticsTab
from tabs.promotion_tab import PromotionTab
from tabs.home_tab import HomeTab
# from tabs.piecharts_tab import PieChartTab

pg.setConfigOptions(antialias=True)
class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Иголки - учёт затрат и продаж")
        self.setGeometry(50, 50, 2220, 1330)
        self.setWindowIcon(QIcon('./logo/logo.png'))
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Вкладка "Траты"
        self.expenses_tab = TabWidget(
            self,
            "expenses.db",
            ["ID", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Дополнительно"],
            self.update_charts,
            tab_type="expenses"  # Тип вкладки "Траты"
        )

        # Вкладка "Доходы"
        self.incomes_tab = TabWidget(
            self,
            "incomes.db",
            ["ID", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Источник", "Ник", "Дополнительно"],
            self.update_charts,
            tab_type="incomes"  # Тип вкладки "Доходы"
        )

        # Вкладка "Склад"
        self.storage_tab = TabWidget(
            self,
            "storage.db",
            ["ID", "Наименование", "Тип", "Размер", "Количество", "Цвет", "Цена", "Дополнительно"],
            self.update_charts,
            tab_type="storage"  # Тип вкладки "Склад"
        )

        self.chart_tab = ChartTab()
        self.summary_tab = SummaryTab()
        self.analytics_tab = AnalyticsTab()
        self.promotion_tab = PromotionTab()
        self.home_tab = HomeTab()

        self.test_list = [self.expenses_tab, self.incomes_tab, self.storage_tab, self.home_tab]

        self.tabs.addTab(self.home_tab, "Главная")
        self.tabs.addTab(self.expenses_tab, "Траты")
        self.tabs.addTab(self.incomes_tab, "Доходы")
        self.tabs.addTab(self.storage_tab, "Склад")
        self.tabs.addTab(self.chart_tab, "Графики доходов")
        self.tabs.addTab(self.summary_tab, "Общие сведения по доходам")
        self.tabs.addTab(self.analytics_tab, "Конверсия")
        self.tabs.addTab(self.promotion_tab, "Заметки")
        self.update_charts()

    def update_charts(self):
        self.chart_tab.plot_data()
        self.summary_tab.update_summary()
        self.home_tab.update_data()  # добавь эту строку

if __name__ == "__main__":
    app = QApplication(sys.argv)
    style = st
    app.setStyleSheet(style)
    window = MainApp()
    window.show()
    sys.exit(app.exec())




