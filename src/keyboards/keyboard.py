from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

register = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text = "Register", callback_data='reg')]
])
parse = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text = "Parse", callback_data='parse')]
])
translatorRU = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text = "to Russian", callback_data='ru')]
])

translatorEN = InlineKeyboardMarkup(inline_keyboard = [
    [InlineKeyboardButton(text = "to English", callback_data='en')]
])