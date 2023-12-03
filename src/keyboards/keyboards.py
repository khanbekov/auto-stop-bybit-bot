# Create your keyboards here.
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_markup = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='/positions'), KeyboardButton(text='/stops')]],
    resize_keyboard=True)
