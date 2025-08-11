import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QLineEdit, QLabel, QComboBox, QMessageBox
)
import datetime
from datetime import date


counter = 0
class TabWidget(QWidget):
    def __init__(self, parent, db_name, columns, update_callback, tab_type):
        super().__init__()
        self.parent = parent
        self.db_name = db_name
        self.columns = columns
        self.update_callback = update_callback
        self.tab_type = tab_type  # Сохраняем тип вкладки
        self.init_db()
        self.init_ui()

    def init_db(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        # Создаем таблицу, если она не существует
        columns_def = ", ".join([f'"{col}" TEXT' for col in self.columns[1:]])
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS data (id INTEGER PRIMARY KEY, {columns_def})")

        # Добавляем новые колонки, если их нет (только для incomes и expenses)
        if (self.tab_type != "storage") and (self.tab_type != "expenses"):  # Не добавляем для storage
            self.cursor.execute("PRAGMA table_info(data)")
            existing_columns = [column[1] for column in self.cursor.fetchall()]

            if "Источник" not in existing_columns:
                self.cursor.execute("ALTER TABLE data ADD COLUMN 'Источник' TEXT")
            if "Ник" not in existing_columns:
                self.cursor.execute("ALTER TABLE data ADD COLUMN 'Ник' TEXT")

        self.conn.commit()

    def init_ui(self):
        layout = QVBoxLayout()
        global counter
        counter += 1
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.columns))
        self.table.setHorizontalHeaderLabels(self.columns)
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 500)
        self.table.setColumnWidth(2, 150)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(7, 150)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.table.cellDoubleClicked.connect(self.handle_cell_click)

        layout.addWidget(self.table)
        self.load_data()

        # Поля для ввода
        self.input_fields = []
        input_layout = QHBoxLayout()

        # Указываем порядок колонок для отображения
        if self.tab_type == "incomes":
            display_columns = ["Наименование", "Дата", "Количество", "Цена", "Стоимость", "Источник", "Ник",
                               "Дополнительно"]
        elif self.tab_type == "expenses":
            display_columns = ["Наименование", "Дата", "Количество", "Цена", "Стоимость", "Дополнительно"]
        elif self.tab_type == "storage":
            display_columns = ["Наименование", "Тип", "Размер", "Количество", "Цвет", "Цена", "Дополнительно"]

        for column in display_columns:
            label = QLabel(column)
            if column == "Источник":
                input_field = QComboBox()
                input_field.addItems(["Авито", "Instagram", "Telegram", "VK", "Знакомые"])
            else:
                input_field = QLineEdit()
                if column == "Дата":
                    today = date.today()
                    input_field.setText(today.strftime("%d.%m.%Y"))  # Форматируем дату в DD.MM.YYYY
                if column == "Количество":
                    input_field.setText('1')
                if column == "Дополнительно":
                    input_field.setPlaceholderText("Не обязательно для заполениня")
                    if self.tab_type == "incomes":
                        input_field = QComboBox()
                        input_field.setEditable(True)
                        self.update_dop_combo(input_field)
                if column == "Ник":
                    input_field.setPlaceholderText("Не обязательно для заполениня")
                if column in ["Количество", "Цена"]:
                    input_field.textChanged.connect(self.calculate_cost)
            input_layout.addWidget(label)
            input_layout.addWidget(input_field)
            self.input_fields.append(input_field)
        layout.addLayout(input_layout)

        # Кнопки
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Добавить")
        self.delete_button = QPushButton("Удалить")
        if counter == 3:
            self.add_button.setText("Добавить на склад")
            self.delete_button.setText("Уменьшить на 1 выделенное")
            self.delete_button.clicked.connect(self.decrement_item)
            self.increment_button = QPushButton("Увеличить на 1 выделенное")
            self.increment_button.clicked.connect(self.increment_item)
            button_layout.addWidget(self.increment_button)
        else:
            self.delete_button.clicked.connect(self.delete_record)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)
        self.add_button.clicked.connect(self.add_record)
        self.setLayout(layout)

        self.scroll_table_to_bottom()

    def handle_cell_click(self, row, column):
        if self.tab_type != "incomes":
            return

        header = self.table.horizontalHeaderItem(column).text()
        if header != "Дополнительно":
            return

        value = self.table.item(row, column).text()

        # Переход в Траты
        # ищем первую Трату с таким наименованием
        conn = sqlite3.connect('expenses.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM data WHERE Наименование = ? ORDER BY id DESC LIMIT 1", (value,))
        result = cursor.fetchone()
        conn.close()

        if result:
            target_id = result[0]
            # теперь находим вкладку Траты и скроллим
            for i in self.parent.test_list:
                if hasattr(i, 'tab_type') and i.tab_type == 'expenses':
                    expenses_tab = i
                    break
            else:
                return

            # переходим на вкладку Траты
            index = self.parent.tabs.indexOf(expenses_tab)
            self.parent.tabs.setCurrentIndex(index)

            # найти строку с этим id
            for row_idx in range(expenses_tab.table.rowCount()):
                row_id = expenses_tab.table.item(row_idx, 0).text()  # id в первом столбце
                if str(row_id) == str(target_id):
                    expenses_tab.table.scrollToItem(expenses_tab.table.item(row_idx, 0))
                    expenses_tab.table.selectRow(row_idx)
                    break

    def update_dop_fields(self):
        # Обновляем ComboBox только если это "incomes"
        if self.tab_type == "incomes":
            for field, column in zip(self.input_fields,
                                     ["Наименование", "Дата", "Количество", "Цена", "Стоимость", "Источник", "Ник",
                                      "Дополнительно"]):
                if column == "Дополнительно" and isinstance(field, QComboBox):
                    self.update_dop_combo(field)

    def update_dop_combo(self, combo):
        try:
            conn = sqlite3.connect('expenses.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, Наименование FROM data ORDER BY id DESC LIMIT 5")
            rows = cursor.fetchall()
            combo.clear()
            for row in rows:
                id_, name = row
                combo.addItem(f"{name} (Траты {id_ - 5})")  # Более понятный формат
            conn.close()
        except Exception as e:
            print(f"Ошибка обновления Дополнительно ComboBox: {e}")

    def scroll_table_to_bottom(self):
        """Прокручивает таблицу в самый низ"""
        if self.table.rowCount() > 0:
            # Прокрутка к последней строке
            self.table.scrollToBottom()

    def load_data(self):
        self.table.setRowCount(0)

        # Указываем порядок колонок для отображения
        if self.tab_type == "incomes":
            # Порядок колонок в SQL-запросе
            sql_columns = ["id", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Источник", "Ник",
                           "Дополнительно"]
            # Порядок колонок для отображения в таблице
            display_columns = ["ID", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Источник", "Ник",
                               "Дополнительно"]
        elif self.tab_type == "expenses":
            sql_columns = ["id", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Дополнительно"]
            display_columns = ["ID", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Дополнительно"]
        elif self.tab_type == "storage":
            sql_columns = ["id", "Наименование", "Тип", "Размер", "Количество", "Цвет", "Цена", "Дополнительно"]
            display_columns = ["ID", "Наименование", "Тип", "Размер", "Количество", "Цвет", "Цена", "Дополнительно"]

        # Формируем SQL-запрос с явным указанием колонок
        query = f"SELECT {', '.join(sql_columns)} FROM data"

        # Получаем данные из базы данных
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        # Заполняем таблицу
        for row_index, row_data in enumerate(rows):
            self.table.insertRow(row_index)
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                self.table.setItem(row_index, col_index, item)

        # Скрываем колонку ID (если нужно)
        self.table.setColumnHidden(0, True)

    def add_record(self):
        if self.add_button.text() == "Добавить на склад":
            print('Добавление на склад')
            values = [field.text().strip() for field in self.input_fields]
            print(values)

            # Указываем порядок колонок для склада
            db_columns = ["ID", "Наименование", "Тип", "Размер", "Количество", "Цвет", "Цена", "Дополнительно"]

            # Проверяем, что количество значений соответствует количеству колонок
            if len(values) != len(db_columns) - 1:  # -1, потому что ID не передается вручную
                print(
                    f"Ошибка: Количество значений ({len(values)}) не соответствует количеству колонок ({len(db_columns) - 1}).")
                return

            if all(values):
                placeholders = ", ".join(["?"] * len(values))
                try:
                    columns_str = ", ".join([f'"{col}"' for col in db_columns[1:]])  # Исключаем ID
                    self.cursor.execute(f'INSERT INTO data ({columns_str}) VALUES ({placeholders})', values)
                    self.conn.commit()
                    self.load_data()
                    for i in self.parent.test_list:
                        if hasattr(i, 'update_callback'):
                            i.update_callback()


                    if self.tab_type == "incomes" and hasattr(self.parent, 'analytics_tab'):
                        self.parent.analytics_tab.update_table()
                except sqlite3.Error as e:
                    print(f"Ошибка базы данных: {e}")

                # Очищаем поля ввода
                for field in self.input_fields:
                    field.clear()
                self.input_fields[self.columns.index("Количество")].setText('1')
        else:
            # Собираем значения из полей ввода
            values = [field.text().strip() if not isinstance(field, QComboBox) else field.currentText() for field in
                      self.input_fields]
            # Преобразуем дату в формат YYYY-MM-DD (если это не склад)
            if self.tab_type != "storage":
                day, month, year = values[1].split('.')
                values[1] = f"{year}-{month}-{day}"

            # Заполняем пустые значения
            if not values[-1]:
                values[-1] = '-'
            if not values[-2]:
                values[-2] = '-'
            if not values[2]:
                values[2] = 1

            # Указываем порядок колонок в базе данных
            if self.tab_type == "incomes":
                db_columns = ["ID", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Дополнительно",
                              "Источник", "Ник"]
            elif self.tab_type == "expenses":
                db_columns = ["ID", "Наименование", "Дата", "Количество", "Цена", "Стоимость", "Дополнительно"]
            elif self.tab_type == "storage":
                db_columns = ["ID", "Наименование", "Тип", "Размер", "Количество", "Цвет", "Цена", "Дополнительно"]

            # Создаем словарь для соответствия имени колонки и её значения
            input_data = {col: val for col, val in zip(self.columns[1:], values)}

            # Собираем значения в порядке, соответствующем базе данных
            ordered_values = [input_data[col] for col in db_columns[1:]]

            if all(ordered_values):
                placeholders = ", ".join(["?"] * len(ordered_values))
                try:
                    columns_str = ", ".join([f'"{col}"' for col in db_columns[1:]])
                    self.cursor.execute(f'INSERT INTO data ({columns_str}) VALUES ({placeholders})', ordered_values)
                    self.conn.commit()
                    self.load_data()
                    for i in self.parent.test_list:
                        i.update_callback()
                        if i.tab_type == 'incomes':
                            i.update_dop_fields()
                except sqlite3.Error as e:
                    print(f"Ошибка базы данных: {e}")
                for field in self.input_fields:
                    if isinstance(field, QLineEdit):
                        field.clear()
                    elif isinstance(field, QComboBox):
                        field.setCurrentIndex(0)
            self.input_fields[self.columns[1:].index("Количество")].setText('1')
            if self.tab_type != "storage":
                self.input_fields[self.columns[1:].index("Дата")].setText(datetime.datetime.now().strftime("%d.%m.%Y"))


    def delete_record(self):
        print('Функция: Удаление')
        selected_row = self.table.currentRow()
        if selected_row >= 0:
            try:
                # Получаем ID из скрытой колонки
                record_id_item = self.table.item(selected_row, 0)  # Колонка с ID (скрытая)

                if record_id_item is None:
                    print("Ошибка: Не удалось получить ID записи.")
                    return

                record_id = record_id_item.text()  # Преобразуем ID в строку
                record_name = self.table.item(selected_row, 1).text()
                print(f"ID записи для удаления: {record_id}")

                # Проверяем, что record_id не пустой
                if not record_id:
                    print("Ошибка: ID записи пустой.")
                    return

                # Запрашиваем подтверждение удаления
                confirm = QMessageBox.question(self, 'Подтверждение удаления',
                                               f"Вы уверены, что хотите удалить запись {record_name}?",
                                               QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                               QMessageBox.StandardButton.No)

                if confirm == QMessageBox.StandardButton.Yes:
                    # Выполняем запрос на удаление
                    self.cursor.execute("DELETE FROM data WHERE id = ?", (record_id,))
                    self.conn.commit()

                    # Обновляем данные в таблице
                    self.load_data()

                    # Обновляем другие элементы интерфейса (если нужно)
                    for i in self.parent.test_list:
                        if hasattr(i, 'update_callback'):
                            i.update_callback()
                        if i.tab_type == 'incomes':
                            i.update_dop_fields()
                    if self.tab_type == "incomes" and hasattr(self.parent, 'analytics_tab'):
                        self.parent.analytics_tab.update_table()

                    print(f"Запись с ID {record_id} успешно удалена.")
                else:
                    print("Удаление отменено пользователем.")
            except sqlite3.Error as e:
                print(f"Ошибка базы данных: {e}")
        else:
            print("Ошибка: Не выбрана строка для удаления.")

    def decrement_item(self):
        print('Функция: Уменьшаем на 1')
        selected_row = self.table.currentRow()
        print(f"Выбрана строка: {selected_row + 1}")
        if selected_row >= 0:
            try:
                # Получаем id записи из скрытой колонки
                id_item = self.table.item(selected_row, 0)  # Колонка с id (скрытая)
                if id_item is None:
                    print("Ошибка: Ячейка с id не найдена.")
                    return

                record_id = int(id_item.text())  # Преобразуем id в число
                print(f"ID записи: {record_id}")

                # Получаем значение "Количество" из таблицы
                quantity_col_index = self.columns.index("Количество")
                quantity_item = self.table.item(selected_row, quantity_col_index)
                if quantity_item is None:
                    print("Ошибка: Ячейка 'Количество' не найдена.")
                    return

                current_quantity = int(quantity_item.text())
                print(f'Было количество: {current_quantity}')

                # Уменьшаем значение на 1, если оно больше 0
                if current_quantity > 0:
                    new_quantity = current_quantity - 1
                    # Обновляем значение в таблице
                    quantity_item.setText(str(new_quantity))

                    # Обновляем значение в базе данных по id
                    self.cursor.execute("UPDATE data SET Количество = ? WHERE id = ?", (new_quantity, record_id))
                    self.conn.commit()
                    print("Количество уменьшено.")

                    # Обновляем другие элементы интерфейса, если необходимо
                    for i in self.parent.test_list:
                        if hasattr(i, 'update_callback'):
                            i.update_callback()
                else:
                    print("Количество уже равно 0, уменьшение невозможно.")
            except sqlite3.Error as e:
                print(f"Ошибка базы данных: {e}")
            except ValueError as e:
                print(f"Ошибка преобразования числа: {e}")
            except Exception as e:
                print(f"Неизвестная ошибка: {e}")

    def increment_item(self):
        print('Функция: Увеличиваем на 1')
        selected_row = self.table.currentRow()
        print(f"Выбрана строка: {selected_row + 1}")
        if selected_row >= 0:
            try:
                # Получаем id записи из скрытой колонки
                id_item = self.table.item(selected_row, 0)  # Колонка с id (скрытая)
                if id_item is None:
                    print("Ошибка: Ячейка с id не найдена.")
                    return

                record_id = int(id_item.text())  # Преобразуем id в число
                print(f"ID записи: {record_id}")

                # Получаем значение "Количество" из таблицы
                quantity_col_index = self.columns.index("Количество")
                quantity_item = self.table.item(selected_row, quantity_col_index)
                if quantity_item is None:
                    print("Ошибка: Ячейка 'Количество' не найдена.")
                    return

                current_quantity = int(quantity_item.text())
                print(f'Было количество: {current_quantity}')

                # Увеличиваем значение на 1
                new_quantity = current_quantity + 1
                # Обновляем значение в таблице
                quantity_item.setText(str(new_quantity))

                # Обновляем значение в базе данных по id
                self.cursor.execute("UPDATE data SET Количество = ? WHERE id = ?", (new_quantity, record_id))
                self.conn.commit()
                print("Количество увеличено.")

                # Обновляем другие элементы интерфейса, если необходимо
                for i in self.parent.test_list:
                    if hasattr(i, 'update_callback'):
                        i.update_callback()
            except sqlite3.Error as e:
                print(f"Ошибка базы данных: {e}")
            except ValueError as e:
                print(f"Ошибка преобразования числа: {e}")
            except Exception as e:
                print(f"Неизвестная ошибка: {e}")

    def calculate_cost(self):
        try:
            # Получаем индекс для "Количество" и "Цена"
            quantity_index = self.columns[1:].index("Количество")
            price_index = self.columns[1:].index("Цена")
            cost_index = self.columns[1:].index("Стоимость")

            # Получаем значения из полей ввода
            quantity = int(self.input_fields[quantity_index].text())
            price = float(self.input_fields[price_index].text())

            # Устанавливаем значение в поле "Стоимость"
            self.input_fields[cost_index].setText(str(quantity * price))
        except (ValueError, IndexError):
            pass