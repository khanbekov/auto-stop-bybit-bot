# Auto stops by ROI Telegram Bot

![aiogram](https://img.shields.io/badge/python-v3.10-blue.svg?logo=python&logoColor=yellow) ![aiogram](https://img.shields.io/badge/aiogram-v3-blue.svg?logo=telegram) ![License](https://img.shields.io/badge/license-MIT-blue.svg)

## About:
Бот для установки и автоматического контроля стопов по ROI. Основной фишкой бота является установка одного стопа для
нескольких позиций. В таком случае, будет проверяться сумма ROI по указанным позициям. Поддерживает как стоп на 
повышение ROI, так и на понижение ROI. Режим выбирается автоматически, исходя из текущего ROI по позициям 
(если позиций ещё нет, то считается, что их ROI равен нулю). 

## Features

The bot provides the following features:

- Установка стопа по ROI для нескольких позиций, по суммарному ROI
- Автоматическая проверка позиций на бирже
- Получение позиций из бирж

## Commands

The bot has several commands that can be used to access its features:


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

## Requirements

- Python v3.10
- aiogram v3.2.0
- dotenv v1.0.0
- ccxt v4.1.64
- sqlalchemy v2.0.23

## Installation

To get started with this bot, follow these steps:

- Clone this repository to your local machine.

    ```
    $ git clone [source]
    ```

- Create a virtual environment, activate it and install required dependencies.

    ```
    $ python3.10 -m venv env
    $ source env/bin/activate
    $ pip install -r requirements/local.txt
    ```

- Create a new bot on Telegram by talking to the BotFather, and [obtain the API token](https://www.siteguarding.com/en/how-to-get-telegram-bot-api-token).

- Rename the file `.env.dist` to `.env` and replace the placeholders with required data.

- Run the bot using `python bot.py`.

