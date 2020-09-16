# Пример шлюза с авторизацией и пополнением аккаунта написан на Python3

## Сценарий действий:
* Пользователь зарегистрируется на вашем сервисе.
* Теперь ему необходимо привязать свой аккаунт в блокчейне к аккаунту в вашем сервисе
* Он вводит свой аккаунт в блокчейне
* Эта информация попадает в шлюз авторизации
* Шлюз генерирует одноразовый код и высылает его через блокчейн (с помощью операции send_message) на указанный аккаунт. Сообщение зашифровано, и поэтому может быть прочитано только получателем.
* После того, как пользователь посмотрел в блокчейне одноразовый код, он вводит его в вашем сервисе, и если он совпадает, с тем что был сгенерирован, то блокчейн аккаунт привязывается к игровому. Шлюз должен проверять, что блокчейн аккаунт привязан только к одному аккаунту.
* После того как аккаунт привязан, пользователю в его личном кабинете сервиса показываем 2 кнопки - пополнить счёт и вывести средства. При этом курс пополнения и вывода могут быть разными.
* При нажатии на кнопку пополнения счёта нужно показать пользователю такое сообщение: чтобы пополнить игровой счёт выполните перевод CWD на такой-то аккакнут. (Здесь указать аккаунт шлюза в crowdwiz)
* Затем пользователь делает перевод на платформе crowdwiz на указанный аккаунт
* Шлюз раз в 60 секунд проверяет историю операций и как только обнаруживает перевод на свой счёт с привязанного аккаунта - выполняет пополнение внутреннего счёта.
* Пользователь выполняет действия в вашем сервисе, с любой логикой и как-то увеличивает или уменьшает свой баланс. 
* Пользователь решил вывести внутренние средства сервиса в CWD - он нажимает в личном кабинете вывести средства
* Ваш сервис даёт шлюзу команду на вывод, и шлюз осуществляет вывод игровой валюты в CWD с помощью стандартной операции transfer.

В данном пример весь интерфейс реализован в виде телеграм-бота

## Необходимые библиотеки:
```bash
pip3 install wheel 
pip3 install peewee psycopg2-binary tornado requests 
pip3 install -U requests[socks]
pip3 --no-cache-dir install crowdwiz
```
В качестве интерфейса для баз данных используется PeeWee он не зависит от движка баз данных, в примере я использую локальную базу, но можно и Postgres

## В комплекте 4 файла:
1) config.py - конфигурационный файл, в нём хранятся все настройки и в нём нужно указать логин шлюза, а также его активный приватный ключ и приватный ключ примечаний, также там нужно указат ключ телеграм бота. Бота можно зарегистрировать через @BotFather. Также в конфиге есть параметры подключения к базе данных и настройки прокси для серверов телеграма (потому что в России эти сервера часто забанены). Также параметры deposit_rate и withdraw_rate тоже хранятся в этом файле. В продакшне вместо конфига скорее всего нужно использовать базу данных!
2) models.py - описывает 3 таблицы, в одной хранятся параметры бота, во втрой пользователи и их локальные балансы, а в третей история пополнений
3) server.py - собственно сам шлюз, который в качестве фронтенда, просто для демонстрационных целей использует телеграм, однако вы можете использовать любой другой фронтенд и бэкенд, но принцип работы будет точно такой же и все функции можно легко адаптировать.
4) telegram_common.py - содержит в себе базовые функции для написания телеграм бота

## Запуск бота:
- Сначала нужно заполнить config.py
- Затем запустить файл python3 models.py он создаст необходимые базы данных и таблицы
- Затем запускаем python3 server.py и можно играться
