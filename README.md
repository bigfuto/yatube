## Социальная сеть для публикации личных дневников YaTube
### Описание
Пользователи могут:
 - Pарегистрироваться
 - Немного написать и при желании показать
 - Подписываться на других авторов
 - Следить за интересными авторами
 - Оставлять коммментарии
 - И конечно просматривать все записи
### Технологии
 - Python 3.7
 - Django 2.2
 - Pillow 8.3
 - Unittest
### Запуск проекта:
 - склонируйте репозиторий:
 ```
 git clone https://github.com/bigfuto/yatube.git
 ```
 - В папке с проектом создайте и активируйте виртуальное окружение с python 3.7:
 ```
 python3 -m venv venv
 . venv/Scripts/activate
 ```
 - Установите зависимости:
 ```
 python3 -m pip install --upgrade pip
 pip install -r requirements.txt 
 ```
 - Перейдите в папку с Django и выполните миграции:
 ```
 cd yatube
 python3 manage.py migrate
 ```
 - При необходимости создайте суперпользователя, для доступа в административную часть:
 ```
 python3 manage.py createsuperuser
 python3 manage.py collectstatic --no-input 
 ```
 - Заупустите dev сервер:
 ```
 python3 manage.py runserver
 ```
 - Проект доступен:
 ```
 http://127.0.0.1:8000/ - проект
 http://127.0.0.1:8000/admin - административная часть
 ```
 - Запуск тестов:
 ```
 python3 manage.py test -v 2
 cd ..
 pytest
 ```
### Автор
[Иванов Илья](https://github.com/bigfuto) в рамках курса Яндекс.Практикума
