from aiogram import html, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ParseMode
from telethon import TelegramClient
from aiogram.fsm.state import State, StatesGroup
from aiogram.methods.get_chat import GetChat
from aiogram.fsm.context import FSMContext
from deep_translator import GoogleTranslator
from langdetect import detect
from config import TELEGRAM_API_HASH, TELEGRAM_API_ID, SESSION_NAME
from src.db.db import usersAndChannels

import src.keyboards.keyboard as kb

router = Router()
dbAgent = usersAndChannels()

api_id = TELEGRAM_API_ID
api_hash = TELEGRAM_API_HASH
session_name = SESSION_NAME

class AwaitMessages(StatesGroup):
    uid_add = State()
    channels_add = State()
    channels_deleting = State()
   
async def parser(chat_name, limit):
    async with TelegramClient(session_name, api_id, api_hash) as client:
        try:
            chat_info = await client.get_entity(chat_name)
            msg = await client.get_messages(entity=chat_info, limit=limit)
            return ({"messages": msg, "channel": chat_info})
        except:
            return "error"

async def translatorFunc(text, lang):
    translated = GoogleTranslator(source='auto', target=lang).translate(text) 
    return translated

async def get_tranalsted_links(text, entities, lang): 
    arr_links = []
    urls_list = []
    texts_to_urls_list = []
    for item in entities:
        if item.type == "text_link":
            begin = (item.offset)
            end = begin + int(item.length)
            texts_to_urls_list.append(text[begin:end])
            urls_list.append(item.url)
    links_to_send_html = []
    for i,item in enumerate(texts_to_urls_list):
        text = await translatorFunc(item, lang)
        rem = f"<a href='{urls_list[i]}'>{text}</a>"
        links_to_send_html.append(rem)
    for i in range(len(links_to_send_html)):
        arr_links.append(links_to_send_html[i])
    return arr_links

#Получение текста после парсинга с ссылками
async def get_linked_messages(text, entities):
    urls_list = []
    texts_to_urls_list = []
    none_linked_text = []
    for item in entities:
        if item["_"] == "MessageEntityTextUrl":
            begin = int(item["offset"])
            end = begin + int(item["length"])
            texts_to_urls_list.append(text[begin:end])
            urls_list.append(item["url"])
            none_linked_text.append((begin, end))
    links_to_send = []
    for i,item in enumerate(texts_to_urls_list):
        rem = f"<a href='{urls_list[i]}'>{item}</a>"
        links_to_send.append(rem)
    s = ""
    j = 0
   
    for i in range(len(none_linked_text)):
        if i == 0:
            s += text[:none_linked_text[i][0]]
        else:
            s += text[none_linked_text[i-1][1]:none_linked_text[i][0]]
        s += links_to_send[j]
        j+=1
    try:
        s += text[none_linked_text[-1][1]:]
        return s
    except:
        return "err"

@router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)} this is a simple bot to keep-up with news\nClick button to register", reply_markup=kb.register)
    await state.set_state(AwaitMessages.uid_add)
    await state.update_data(uid = message.chat.id)

#callback register
@router.callback_query(F.data == 'reg')
async def echo_handler(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    res = await dbAgent.add_users_table(data['uid']) 
    if res != "repeat":
        await callback.answer("Succeseful")
        
    else:
        await callback.answer("You already in system")
    await callback.message.answer("Now you can send me channel links in format @channel_name\nSay 'enough' to stop or skip")
    await state.set_state(AwaitMessages.channels_add)
    await state.update_data(channels = [])


#adding channels by user
@router.message(AwaitMessages.channels_add, F.text.casefold().startswith("@"))
async def echo_handler(message: Message, state: FSMContext) -> None:
    if(message.text.startswith("@")):
        data = await state.get_data()
        data['channels'].append(message.text)
        await state.set_data(data)

#callback register
@router.message(AwaitMessages.channels_add, F.text.casefold() == "enough")
async def echo_handler(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    for item in data["channels"]:
        await dbAgent.add_channels_by_uid(message.chat.id, item)
    await message.answer("OK\nLet's parse or view list of your channels", reply_markup=kb.parseAndview)
    
    
#callback parse messages
@router.callback_query(F.data == 'parse')
async def echo_handler(callback: CallbackQuery, state: FSMContext) -> None:
    channels = await dbAgent.get_channels_by_uid(callback.message.chat.id)
    for item in channels:
        res =  await parser(item[0], 1)
        if res != "error":
            text = res["messages"][0].to_dict()['message']
            entities = res["messages"][0].to_dict()['entities']
            msg = await get_linked_messages(text, entities)
            if msg != "err":
                if not(item[0] in msg):
                    msg += "\n" + item[0] + "\n"
                if detect(msg) == 'ru':
                    await callback.message.answer(msg, reply_markup = kb.translatorEN, parse_mode=ParseMode.HTML)
                else:
                    await callback.message.answer(msg, reply_markup = kb.translatorRU, parse_mode=ParseMode.HTML)
            else:
                continue 
        else:
            await callback.message.answer(f"Something went wrong with channel {item[0]}\nI will delete this from table")
            await state.set_state(AwaitMessages.channels_deleting)
            await state.update_data(uidAndChannel= (callback.message.chat.id, item[0]))
            channels = await state.get_data()
            await dbAgent.delete_channels_by_uid(channels['uidAndChannel'][0],channels['uidAndChannel'][1])
            await state.clear()
    await callback.message.answer(f"If you want to parse again or view list of channes click buttons below", reply_markup=kb.parseAndview)
    await callback.message.answer(f"If you want to add more channels click button below", reply_markup=kb.addMore)
    
    
#callback add more channels
@router.callback_query(F.data == 'add')
async def echo_handler(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer("Now you can send me channel links in format @channel_name\nSay 'enough' to stop or skip")
    await state.set_state(AwaitMessages.channels_add)
    await state.update_data(channels = [])
  
  
#callback view channels list by uid
@router.callback_query(F.data == 'show')
async def echo_handler(callback: CallbackQuery, state: FSMContext) -> None:
    channels = await dbAgent.get_channels_by_uid(callback.message.chat.id)
    for item in channels:
        await callback.message.answer(f"{item[0]}\n")
    await callback.message.answer(f"If you want to parse click button below", reply_markup=kb.parse)
    await callback.message.answer(f"If you want to add more channels click button below", reply_markup=kb.addMore)
        
#callback tranclate to ru
@router.callback_query(F.data == 'change')
async def echo_handler(callback: CallbackQuery, ) -> None:
    text = callback.message.text
    entities = callback.message.entities
    if(detect(text) == 'en'):
        links = await get_tranalsted_links(text, entities, 'ru')
        tranlated = await translatorFunc(callback.message.text ,'ru')
        await callback.message.reply(tranlated + "\n" + "\n".join(links), parse_mode=ParseMode.HTML)
    else: 
        await callback.answer("Already in chosen language!")
            
#callback tranclate to ru
@router.callback_query(F.data == 'ru')
async def echo_handler(callback: CallbackQuery, ) -> None:
    text = callback.message.text
    entities = callback.message.entities
    if(detect(text) == 'en'):
        links = await get_tranalsted_links(text, entities, 'ru')
        tranlated = await translatorFunc(callback.message.text ,'ru')
        await callback.message.reply(tranlated + "\n" + "\n".join(links), parse_mode=ParseMode.HTML)
    else: 
        await callback.answer("Already in chosen language!")

#callback tranclate to en
@router.callback_query(F.data == 'en')
async def echo_handler(callback: CallbackQuery, ) -> None:
    text = callback.message.text
    entities = callback.message.entities
    if(detect(text) == 'ru'):
        links = await get_tranalsted_links(text, entities, 'en')
        tranlated = await translatorFunc(callback.message.text ,'en')
        await callback.message.reply(tranlated + "\n" + "\n".join(links), parse_mode=ParseMode.HTML)
    else: 
        await callback.answer("Already in chosen language!")