import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox,
    QScrollArea, QMenuBar, QMessageBox, QFrame, QStackedWidget, QHBoxLayout, QFileDialog,
    QTextEdit, QDialog
)
from PyQt5.QtGui import QCursor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from models import User, GameNews, NewsImage, init_db, get_session, NewsView
from datetime import datetime

class StyledWidget:
    base_font = "Arial"
    base_font_size = 14

    def get_button_style(self):
        return '''
            QPushButton {
                background-color: #3a7bd5;
                color: white;
                font-family: Arial;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px 12px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #3572c4;
            }
            QPushButton:pressed {
                background-color: #2f65aa;
            }
        '''

    def get_label_style(self, bold=False):
        return f'''
            QLabel {{
                font-family: '{self.base_font}';
                font-size: {self.base_font_size}px;
                color: #333;
                {'font-weight: bold;' if bold else ''}
                margin: 5px 0;
            }}
        '''

    def create_label(self, text, bold=False, alignment=None):
        label = QLabel(text)
        label.setStyleSheet(self.get_label_style(bold=bold))
        if alignment:
            label.setAlignment(alignment)
        return label

    def create_input(self, placeholder="", password=False):
        line_edit = QLineEdit(placeholderText=placeholder)
        line_edit.setStyleSheet(f"font-family: {self.base_font}; font-size: {self.base_font_size}px; padding: 5px; margin:5px 0;")
        if password:
            line_edit.setEchoMode(QLineEdit.Password)
        return line_edit

    def create_button(self, text, callback=None):
        button = QPushButton(text)
        button.setStyleSheet(self.get_button_style())
        if callback:
            button.clicked.connect(callback)
        return button

# окно авторизации
class AuthApp(QWidget, StyledWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизация')
        self.resize(350, 350)
        self.engine = init_db()
        self.session = get_session(self.engine)
        self.mode = 'login'
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignCenter)

        self.header_label = self.create_label("Авторизация", bold=True, alignment=Qt.AlignCenter)
        self.username_input = self.create_input("Имя пользователя")
        self.password_input = self.create_input("Пароль", password=True)
        self.secret_key_input = self.create_input("Секретный ключ (для Админа, опционально)", password=True)
        self.secret_key_input.hide()

        self.login_button = self.create_button('Войти', self.handle_action)
        self.register_button = self.create_button('Регистрация', self.toggle_mode)
        self.message_label = self.create_label("", alignment=Qt.AlignCenter)

        self.layout.addWidget(self.header_label)
        self.layout.addWidget(self.username_input)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.secret_key_input)
        self.layout.addWidget(self.login_button)
        self.layout.addWidget(self.register_button)
        self.layout.addWidget(self.message_label)

        self.setLayout(self.layout)

    def toggle_mode(self):
        if self.mode == 'login':
            self.mode = 'register'
            self.header_label.setText("Регистрация")
            self.login_button.setText("Зарегистрироваться")
            self.register_button.setText("Назад к авторизации")
            self.secret_key_input.show()
            self.message_label.setText("")
        else:
            self.mode = 'login'
            self.header_label.setText("Авторизация")
            self.login_button.setText("Войти")
            self.register_button.setText("Регистрация")
            self.secret_key_input.hide()
            self.secret_key_input.clear()
            self.message_label.setText("")

    def handle_action(self):
        if self.mode == 'login':
            self.login()
        else:
            self.register()

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        user = self.session.query(User).filter_by(username=username, password=password).first()
        if user:
            self.close()
            self.main_app = MainApp(user, self.session)
            self.main_app.show()
        else:
            self.message_label.setText('Неверное имя пользователя или пароль.')

    def register(self, username=None, password=None, secret_key=None, show_message=True):
        if username is None:
            username = self.username_input.text()
        if password is None:
            password = self.password_input.text()
        if secret_key is None:
            secret_key = self.secret_key_input.text()

        if not username or not password:
            if show_message:
                self.message_label.setText('Пожалуйста, заполните все поля.')
            return

        if self.session.query(User).filter_by(username=username).first():
            if show_message:
                self.message_label.setText('Пользователь уже существует.')
            return

        role = "Admin" if secret_key == "SECRET_KEY" else "Пользователь"
        new_user = User(username=username, password=password, role=role)
        self.session.add(new_user)
        self.session.commit()
        if show_message:
            self.message_label.setText('Регистрация успешна! Переключитесь назад к авторизации.')


# окно информации о пользователе
class UserInfoWindow(QWidget, StyledWidget):
    def __init__(self, user, main_app=None):
        super().__init__()
        self.setWindowTitle("Информация о пользователе")
        self.resize(300, 200)
        self.user = user
        self.main_app = main_app
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.create_label(f"Логин: {self.user.username}", bold=True))
        layout.addWidget(self.create_label(f"Дата регистрации: {self.user.registration_date.strftime('%Y-%m-%d %H:%M:%S')}"))
        layout.addWidget(self.create_label(f"Роль: {self.user.role}"))

        if self.main_app:
            logout_button = self.create_button("Выйти из аккаунта", self.logout)
            layout.addWidget(logout_button)

        self.setLayout(layout)

    def logout(self):
        if self.main_app:
            self.main_app.logout()
            self.close()

# окно статистики приложения
class StatisticsWindow(QWidget, StyledWidget):
    def __init__(self, session):
        super().__init__()
        self.setWindowTitle("Статистика приложения")
        self.resize(300, 300)
        self.session = session
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        layout = QVBoxLayout()

        user_count = self.session.query(User).count()
        news_count = self.session.query(GameNews).count()
        views_count = self.session.query(NewsView).count()
        images_count = self.session.query(NewsImage).count()
        admins_count = self.session.query(User).filter_by(role='Admin').count()
        regular_users_count = self.session.query(User).filter_by(role='Пользователь').count()

        layout.addWidget(self.create_label(f"Количество пользователей: {user_count}", bold=True))
        layout.addWidget(self.create_label(f"Количество администраторов: {admins_count}"))
        layout.addWidget(self.create_label(f"Количество обычных пользователей: {regular_users_count}"))
        layout.addWidget(self.create_label(f"Количество новостей: {news_count}", bold=True))
        layout.addWidget(self.create_label(f"Всего просмотров новостей: {views_count}", bold=True))
        layout.addWidget(self.create_label(f"Количество изображений к новостям: {images_count}", bold=True))

        self.setLayout(layout)

# окно добавления новости в приложении
class AddNewsWindow(QWidget, StyledWidget):
    def __init__(self, session, user, on_news_added):
        super().__init__()
        self.setWindowTitle("Добавить новость")
        self.resize(400, 300)
        self.session = session
        self.user = user
        self.on_news_added = on_news_added
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(self.create_label("Добавление новости:", bold=True))
        self.title_input = self.create_input("Заголовок новости")
        self.content_input = self.create_input("Содержание новости")
        self.category_selector = QComboBox()
        self.category_selector.addItems(["Обновления", "Релизы", "Технические новости"])
        self.category_selector.setStyleSheet(self.get_label_style())

        self.game_selector = QComboBox()
        self.game_selector.setStyleSheet(self.get_label_style())
        self.game_selector.addItems(["", "CS2", "DOTA2", "Deadlock"])

        save_button = self.create_button("Сохранить", self.save_news)
        self.message_label = self.create_label("")

        layout.addWidget(self.title_input)
        layout.addWidget(self.content_input)
        layout.addWidget(self.category_selector)
        layout.addWidget(QLabel("Игра (опционально):"))
        layout.addWidget(self.game_selector)
        layout.addWidget(save_button)
        layout.addWidget(self.message_label)

        self.setLayout(layout)

    def save_news(self):
        title = self.title_input.text()
        content = self.content_input.text()
        category = self.category_selector.currentText()
        game = self.game_selector.currentText().strip()

        if not title or not content:
            self.message_label.setText("Пожалуйста, заполните все поля.")
            return

        if game == "":
            game = None

        new_news = GameNews(title=title, content=content, category=category, author_id=self.user.id, game=game)
        self.session.add(new_news)
        self.session.commit()

        self.message_label.setText("Новость успешно добавлена!")
        self.on_news_added()
        self.close()

# кликается, ура!
class ClickableNewsWidget(QFrame, StyledWidget):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()

# основное окно со всем
class MainApp(QMainWindow, StyledWidget):
    def __init__(self, user, session):
        super().__init__()
        self.user = user
        self.session = session
        self.setWindowTitle('Новости')
        self.resize(800, 600)
        self.init_ui()
        self.setStyleSheet("background-color: #f0f0f0;")

        self.current_images = []
        self.current_image_index = 0
        self.current_news = None

    def init_ui(self):
        menu_bar = QMenuBar(self)

        # Создаем контейнер для правого верхнего угла, чтобы разместить статистику(для админа) и иконку пользователя
        top_right_widget = QWidget()
        top_right_layout = QHBoxLayout()
        top_right_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.user.role == "Admin":
            self.stats_button = self.create_button("Статистика", self.show_statistics)
            top_right_layout.addWidget(self.stats_button)

        user_icon = self.create_button(f"👤 {self.user.username}", self.show_user_info)
        top_right_layout.addWidget(user_icon)
        top_right_widget.setLayout(top_right_layout)

        menu_bar.setCornerWidget(top_right_widget, Qt.TopRightCorner)
        self.setMenuBar(menu_bar)

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Страница со списком новостей
        self.news_list_widget = QWidget()
        self.news_list_layout = QVBoxLayout(self.news_list_widget)

        top_layout = QHBoxLayout()
        if self.user.role == "Admin":
            self.add_news_button = self.create_button("Добавить новость", self.open_add_news_window)
            top_layout.addWidget(self.add_news_button)
        else:
            spacer = QLabel()
            spacer.setFixedHeight(1)
            top_layout.addWidget(spacer)

        self.category_selector = QComboBox()
        self.category_selector.setStyleSheet(self.get_label_style())
        self.category_selector.addItems(["Все новости", "Обновления", "Релизы", "Технические новости"])
        self.category_selector.currentTextChanged.connect(self.update_news)
        top_layout.addWidget(self.category_selector)

        self.game_selector = QComboBox()
        self.game_selector.setStyleSheet(self.get_label_style())
        self.game_selector.addItems(["Все игры", "CS2", "DOTA2", "Deadlock"])
        self.game_selector.currentTextChanged.connect(self.update_news)
        top_layout.addWidget(self.game_selector)

        self.news_list_layout.addLayout(top_layout)

        self.scroll_area_list = QScrollArea()
        self.scroll_area_list.setWidgetResizable(True)
        self.news_container = QWidget()
        self.news_layout = QVBoxLayout(self.news_container)
        self.news_container.setLayout(self.news_layout)
        self.scroll_area_list.setWidget(self.news_container)
        self.news_list_layout.addWidget(self.scroll_area_list)
        self.stacked_widget.addWidget(self.news_list_widget)

        # Страница детализации новости
        self.news_detail_widget = QWidget()
        self.news_detail_layout = QVBoxLayout(self.news_detail_widget)

        self.detail_scroll_area = QScrollArea()
        self.detail_scroll_area.setWidgetResizable(True)
        self.detail_content_widget = QWidget()
        self.detail_content_layout = QVBoxLayout(self.detail_content_widget)

        self.detail_title = self.create_label("", bold=True)
        
        self.detail_text_view = QTextEdit()
        self.detail_text_view.setReadOnly(True)
        self.detail_text_view.setStyleSheet("padding: 5px; font-size:14px;")
        self.detail_text_view.setFixedHeight(200)

        self.detail_meta = self.create_label("")
        self.detail_author = self.create_label("")
        self.detail_game = self.create_label("")
        self.detail_views = self.create_label("")

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("margin:10px;")

        self.prev_image_button = self.create_button("←", self.show_prev_image)
        self.next_image_button = self.create_button("→", self.show_next_image)

        self.prev_image_button.hide()
        self.next_image_button.hide()

        self.delete_image_button = self.create_button("Удалить изображение", self.delete_current_image)
        self.delete_image_button.hide()

        image_nav_layout = QHBoxLayout()
        image_nav_layout.addWidget(self.prev_image_button)
        image_nav_layout.addWidget(self.image_label, stretch=1)
        image_nav_layout.addWidget(self.next_image_button)

        self.detail_content_layout.addWidget(self.detail_title)
        self.detail_content_layout.addWidget(self.detail_text_view)
        self.detail_content_layout.addWidget(self.detail_meta)
        self.detail_content_layout.addWidget(self.detail_author)
        self.detail_content_layout.addWidget(self.detail_game)
        self.detail_content_layout.addWidget(self.detail_views)
        self.detail_content_layout.addLayout(image_nav_layout)
        self.detail_content_layout.addWidget(self.delete_image_button, alignment=Qt.AlignCenter)

        self.back_button = self.create_button("Назад", self.back_to_list)
        self.add_images_button = self.create_button("Добавить изображения", self.add_images)
        self.add_images_button.hide()

        self.edit_button = self.create_button("Редактировать новость", self.edit_news)
        self.edit_button.hide()

        self.save_changes_button = self.create_button("Сохранить изменения", self.save_changes)
        self.save_changes_button.hide()

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.back_button)
        button_layout.addWidget(self.add_images_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.save_changes_button)
        self.detail_content_layout.addLayout(button_layout)

        self.detail_content_widget.setLayout(self.detail_content_layout)
        self.detail_scroll_area.setWidget(self.detail_content_widget)

        self.news_detail_layout.addWidget(self.detail_scroll_area)
        self.stacked_widget.addWidget(self.news_detail_widget)

        self.load_news()

    def open_add_news_window(self):
        self.add_news_window = AddNewsWindow(self.session, self.user, self.load_news)
        self.add_news_window.show()

    def load_news(self, category=None, game=None):
        for i in reversed(range(self.news_layout.count())):
            widget = self.news_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        query = self.session.query(GameNews)

        if category and category != "Все новости":
            query = query.filter_by(category=category)

        if game and game != "Все игры":
            query = query.filter_by(game=game)

        news_items = query.order_by(GameNews.date_posted.desc()).all()

        if not news_items:
            no_news_label = self.create_label("Нет доступных новостей.", bold=True, alignment=Qt.AlignCenter)
            self.news_layout.addWidget(no_news_label)
            return

        for item in news_items:
            author_name = self.get_author(item.author_id)
            views_count = len(item.views)  # Количество уникальных просмотров

            news_widget = ClickableNewsWidget()
            nw_layout = QVBoxLayout(news_widget)

            title_label = self.create_label(f"Заголовок: {item.title}", bold=True)
            content_label = self.create_label(f"Содержание: {item.content}")
            content_label.setWordWrap(True)
            meta_label = self.create_label(
                f"Категория: {item.category} | Дата: {item.date_posted.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            author_label = self.create_label(f"Автор: {author_name}")
            author_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
            views_label = self.create_label(f"Просмотров: {views_count}")

            # Отображаем игру, если есть
            if item.game:
                game_label = self.create_label(f"Игра: {item.game}")
                nw_layout.addWidget(game_label)

            nw_layout.addWidget(title_label)
            nw_layout.addWidget(content_label)
            nw_layout.addWidget(meta_label)
            nw_layout.addWidget(author_label)
            nw_layout.addWidget(views_label)

            news_widget.setStyleSheet(
                "border: 1px solid #ccc; "
                "border-radius: 5px; "
                "padding: 10px; "
                "margin: 5px; "
                "background-color: #ffffff;"
            )

            def on_clicked(item=item):
                self.show_news_detail(item)

            news_widget.clicked.connect(on_clicked)
            self.news_layout.addWidget(news_widget)

        self.news_layout.addStretch()

    def get_author(self, author_id):
        user = self.session.query(User).filter(User.id == author_id).first()
        return user.username if user else "Неизвестно"

    def show_news_detail(self, news_item):
        self.current_news = news_item
        author_name = self.get_author(news_item.author_id)
        self.detail_title.setText(f"Заголовок: {news_item.title}")
        self.detail_text_view.setReadOnly(True)
        self.detail_text_view.setText(news_item.content)
        self.detail_meta.setText(f"Категория: {news_item.category} | Дата: {news_item.date_posted.strftime('%Y-%m-%d %H:%M:%S')}")
        self.detail_author.setText(f"Автор: {author_name}")

        if news_item.game:
            self.detail_game.setText(f"Игра: {news_item.game}")
        else:
            self.detail_game.setText("Игра: не указано")

        # проверяем просмотры
        already_viewed = self.session.query(NewsView).filter_by(user_id=self.user.id, news_id=news_item.id).first()
        if not already_viewed:
            new_view = NewsView(user_id=self.user.id, news_id=news_item.id)
            self.session.add(new_view)
            self.session.commit()
            self.current_news = self.session.query(GameNews).filter_by(id=news_item.id).one()

        views_count = len(self.current_news.views)
        self.detail_views.setText(f"Просмотров: {views_count}")

        self.current_images = self.current_news.images
        self.current_image_index = 0
        self.update_image_display()

        if self.user.role == "Admin":
            self.add_images_button.show()
            self.edit_button.show()
        else:
            self.add_images_button.hide()
            self.edit_button.hide()

        self.save_changes_button.hide()

        self.stacked_widget.setCurrentWidget(self.news_detail_widget)

    def update_image_display(self):
        if not self.current_images:
            self.image_label.clear()
            self.prev_image_button.hide()
            self.next_image_button.hide()
            self.delete_image_button.hide()
            return

        if self.current_image_index < 0:
            self.current_image_index = 0
        if self.current_image_index >= len(self.current_images):
            self.current_image_index = len(self.current_images) - 1

        img_record = self.current_images[self.current_image_index]
        if os.path.exists(img_record.image_path):
            pix = QPixmap(img_record.image_path)
            self.image_label.setPixmap(pix.scaled(300, 300, Qt.KeepAspectRatio))
        else:
            self.image_label.setText("Изображение не найдено")

        if len(self.current_images) > 1:
            self.prev_image_button.show()
            self.next_image_button.show()
        else:
            self.prev_image_button.hide()
            self.next_image_button.hide()

        if self.user.role == "Admin":
            self.delete_image_button.show()
        else:
            self.delete_image_button.hide()

    def back_to_list(self):
        self.stacked_widget.setCurrentWidget(self.news_list_widget)

    def add_images(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выбрать изображения", "", "Images (*.png *.xpm *.jpg)")
        if files:
            for f in files:
                if os.path.exists(f):
                    new_img = NewsImage(news_id=self.current_news.id, image_path=f)
                    self.session.add(new_img)
            self.session.commit()
            self.current_news = self.session.query(GameNews).filter_by(id=self.current_news.id).one()
            self.show_news_detail(self.current_news)

    def delete_current_image(self):
        if not self.current_images:
            return

        img_to_delete = self.current_images[self.current_image_index]

        reply = QMessageBox.question(self, "Удалить", "Удалить это изображение?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.session.delete(img_to_delete)
            self.session.commit()

            self.current_news = self.session.query(GameNews).filter_by(id=self.current_news.id).one()
            self.current_images = self.current_news.images
            if self.current_image_index >= len(self.current_images):
                self.current_image_index = len(self.current_images) - 1
            self.update_image_display()

    def show_prev_image(self):
        if self.current_images:
            self.current_image_index -= 1
            self.update_image_display()

    def show_next_image(self):
        if self.current_images:
            self.current_image_index += 1
            self.update_image_display()

    def update_news(self):
        category = self.category_selector.currentText()
        if category == "Все новости":
            category = None

        selected_game = self.game_selector.currentText()
        if selected_game == "Все игры":
            selected_game = None

        self.load_news(category, selected_game)

    def show_user_info(self):
        self.user_info_window = UserInfoWindow(self.user, self)
        self.user_info_window.show()

    def logout(self):
        self.close()
        self.auth_window = AuthApp()
        self.auth_window.show()

    def edit_news(self):
        self.detail_text_view.setReadOnly(False)
        self.save_changes_button.show()

    def save_changes(self):
        new_content = self.detail_text_view.toPlainText().strip()
        if not new_content:
            QMessageBox.warning(self, "Ошибка", "Содержимое новости не может быть пустым.")
            return

        self.current_news.content = new_content
        self.session.commit()

        self.detail_text_view.setReadOnly(True)
        self.save_changes_button.hide()

        # Обновляем список новостей и детальный вид
        self.load_news()
        self.show_news_detail(self.current_news)

        QMessageBox.information(self, "Успех", "Изменения сохранены.")

    def show_statistics(self):
        self.stats_window = StatisticsWindow(self.session)
        self.stats_window.show()


# запуск приложения
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AuthApp()
    window.register('admin', 'admin', 'SECRET_KEY',show_message=False)
    window.show()
    sys.exit(app.exec_())
