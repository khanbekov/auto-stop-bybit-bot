# Auto stops by ROI Telegram Bot

![aiogram](https://img.shields.io/badge/python-v3.10-blue.svg?logo=python&logoColor=yellow) ![aiogram](https://img.shields.io/badge/aiogram-v3-blue.svg?logo=telegram) ![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Описание:
Бот для установки и автоматического контроля stop ордеров по ROI. Основной фишкой бота является установка одного стопа для
нескольких позиций. В таком случае, будет проверяться сумма ROI по указанным позициям. Поддерживает как стоп на 
повышение ROI, так и на понижение ROI. Режим выбирается автоматически, исходя из текущего ROI по позициям 
(если позиций ещё нет, то считается, что их ROI равен нулю). 

## Возможности

Бот предоставляет следующие возможности

- Установка стопа по ROI для нескольких позиций, по суммарному ROI;
- Автоматическая проверка позиций на бирже Bybit;
- Получение позиций из биржи Bybit.

## Команды

Бот предоставляет следующие команды для управления:

### Управление стопами 

`/new <тикеры через пробел> <стоп ROI>` - создание нового стопа. Например `/new BTC/USDT:USDT ETH/USDT:USDT 4.0%.`
 Вы можете указывать любое количество тикеров, и для них будет вычисляться суммарный ROI по позициям.
 Для работы стопа, вы должны находиться в позициях по всем перечисленным тикерам, до этого момента он будет простаивать 
 (таким образом, можете создать стоп заранее). Если позиции уже имеются, и указанный ROI меньше, чем текущий ROI позиций, то стоп активируется когда ROI позиций упадет. Также это работает для отрицательного ROI.

`/stops` - выводит список текущих стопов, включая их id, который используется в других командах.

 `/change <id> <новый ROI>`. Например  `/change 2 5%` сменит у стопа с id 2 ROI на 5%. Если текущий ROI позиции 
 больше, то стоп активируется, когда ROI позиции падет. Если текущее значение меньше, то когда поднимется
 (то есть также, как и при создании стопа). 

 `/remove <id>` - удаляет стоп с заданным id.

### Управление ключами 

 `/set_keys <public_key> <private_key>` - Установить новые ключи. 

 `/get_keys` - получить ваши ключи. Private key выводится частично в целях безопасности

 `/check_keys` - проверить работоспособность ключей. Выводит текущий свободный баланс, по которому вы можете проверить, 
 что ключи имеют доступ к верному аккаунту.

### Прочее 

 `/positions` - просмотр текущих позиций на бирже.

## Зависимости

- Python v3.10
- aiogram v3.2.0
- dotenv v1.0.0
- ccxt v4.1.64
- sqlalchemy v2.0.23

## Установка
Запуск был протестирован на Linux Ubuntu 24.04. Предполагаю, что это также будет работать на других версиях Ubuntu 
и других дистрибутивах Linux.

Чтобы запустить бота, следуйте следующим инструкциям:

### Начало установки

- Склонируйте репозиторий на своём компьютере или сервере.

    ```console
    user@server:~$ git clone https://github.com/khanbekov/auto-stop-bybit-bot.git
    user@server:~$ cd auto-stop-bybit-bot
    ```

- Создайте нового бота в Telegram через [BotFather](https://t.me/BotFather), и [получите API токен](https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token).

- Переименуйте файл `.env.dist` в `.env` и вставьте в переменную BOT_TOKEN токен бота. Пример:

    ```
    # Telegram Bot Token
    BOT_TOKEN="123123123:AAAABBBBCCCCDDDDEEEEFFFFGGGG"
    ```

### Запуск через Docker Compose
- Установите Docker сompose, следуя [официальной инструкции](https://docs.docker.com/compose/install/).

- Запустите бота, используя команду:

    ```console
    user@server:~$ docker-compose up
    ```

### Запуск из консоли

- Создайте виртуальную среду (virtual env) и установите зависимости.

    ```console
    user@server:~$ python3.10 -m venv env
    user@server:~$ source env/bin/activate
    user@server:~$ pip install -r requirements/local.txt
    ```

- Запустите бота, используя:

    ```console
    user@server:~$ python bot.py
    ```

### Создание сервиса Systemd
- Создайте файл сервиса:
    ```console
    user@server:~$ sudo vim /etc/systemd/system/auto-stop-bybit-bot.service
    ```
- Заполните файл 
(**Внимание**: вам нужно прописать актуальный путь к файлам в переменных 
**WorkingDirectory** и **ExecStart**):
    ```ini
    [Unit]
    Description=Auto Stop ROI Telegram Bot
    After=network.target
    
    [Service]
    User=user
    WorkingDirectory=/home/user/auto-stop-bybit-bot
    ExecStart=/home/user/auto-stop-bybit-bot/venv/bin/python bot.py
    Restart=always
    
    [Install]
    WantedBy=multi-user.target
    ```
- Запустите сервис:
    ```console
    user@server:~$ sudo systemctl start auto-stop-bybit-bot.service
    ```
#### Подсказка: полезные команды systemctl и journalctl

- Также вы можете проверить состояние работы сервиса:
    ```console
    user@server:~$ sudo systemctl status auto-stop-bybit-bot.service
    ```
- Чтение логов сервиса:
    ```console
    user@server:~$ sudo journalctl -eu auto-stop-bybit-bot.service
    ```
- Остановка сервиса:
    ```console
    user@server:~$ sudo systemctl stop auto-stop-bybit-bot.service
    ```

