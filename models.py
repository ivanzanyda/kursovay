from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    role = Column(String, default='Пользователь')

    def __init__(self, username, password, role='Пользователь'):
        self.username = username
        self.password = password
        self.role = role


class GameNews(Base):
    __tablename__ = 'game_news'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    date_posted = Column(DateTime, default=datetime.utcnow)
    category = Column(String, nullable=False)
    game = Column(String, nullable=True)

    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship('User', backref='news')

    images = relationship('NewsImage', back_populates='news', cascade="all, delete-orphan")
    views = relationship('NewsView', back_populates='news', cascade="all, delete-orphan")


class NewsImage(Base):
    __tablename__ = 'news_images'

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey('game_news.id'))
    image_path = Column(String, nullable=False)

    news = relationship('GameNews', back_populates='images')


class NewsView(Base):
    __tablename__ = 'news_views'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    news_id = Column(Integer, ForeignKey('game_news.id'))
    view_date = Column(DateTime, default=datetime.utcnow)

    news = relationship('GameNews', back_populates='views')
    user = relationship('User', backref='views')


def init_db():
    engine = create_engine('sqlite:///users.db')
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()
