import os
import telebot
from src.utils.dlyoutube import DLYouTube
from src.utils.linkcheck import LinkCheck
from src.utils.database import DataBase
from pytube.exceptions import ExtractError
from telebot import types
from config import CLIENTS, SENDING_QUEUE
import datetime
from dotenv.main import load_dotenv
load_dotenv()

# in different config 
BOT_TOKEN = os.environ['BOT_TOKEN']

print(type(CLIENTS))
print(BOT_TOKEN)

class DownloadBot:
    bot = None
    message = None
    db = None
    ENJOY = None
    rabbit = None
    YT = {}
    IG = {}
    define_type_message = {}
    VID_OR_AUD_MARKUP = {}
    RES_MARKUP = {}
    STOP_MARKUP = {}
    user_data = {}
    stages = {}
    file_id = {}
    url = {}
    stop_msg = {}
    download_msg = {}

    def __init__(self) -> None:

        self.bot = telebot.TeleBot(BOT_TOKEN) 
        @self.bot.message_handler(content_types=["text"])
        def get_text_message_handler(message):
            return self.get_text_messages(message)
        
    def get_text_messages(self, message):
        print("message = ", message.text)

        if message.text == 'stop downloading':
            self.is_stop(message)

        if not message.from_user.id in self.stages:
            self.stages[message.from_user.id] = 'start'

        match self.stages[message.from_user.id]:
            case 'start':
                self.define_type_message[message.from_user.id] = LinkCheck.which_link(message) 
                
                if self.define_type_message[message.from_user.id] == LinkCheck.invalid:
                    self.bot.send_message(message.from_user.id, "Send me a link to a YouTube video e.g.: https://youtu.be/6_uAAzbv4IE?si=d86o8lWCuHnZqKX1")
                    return
                
                self.url[message.from_user.id] = message.text

                self.user_data[message.from_user.id] = {
                    'provider': 'youtube',
                    'user_id': str(message.from_user.id),
                    'username': str(message.from_user.username),
                    'date_time_of_request': '{}'.format(datetime.datetime.now()),
                    'chat_id': str(message.chat.id),
                    'request_url': str(message.text),
                    'time_elapsed': datetime.datetime.now()
                }
                self.VID_OR_AUD_MARKUP[message.from_user.id] = types.ReplyKeyboardMarkup(resize_keyboard=True) 
                video = types.KeyboardButton('video')
                audio = types.KeyboardButton('audio')
                self.VID_OR_AUD_MARKUP[message.from_user.id].add(video, audio)
                self.bot.send_message(message.from_user.id, text="Would you like to get video or audio only?"
                                      .format(message.from_user), reply_markup=self.VID_OR_AUD_MARKUP[message.from_user.id])
                self.bot.register_next_step_handler(message, self.is_video_or_audio) 
            
            case 'is_vid_or_aud':
                self.is_video_or_audio(message)
            
            case 'choose res':
                self.choose_YT_resolution(message)
            
            case 'download':
                self.download(message)


    def is_video_or_audio(self, message):
        self.stages[message.from_user.id] = 'is_vid_or_aud'
        match message.text:
            case 'video':
                SENDING_QUEUE.append(message.from_user.id)
                self.user_data[message.from_user.id]['video_or_audio'] = 'video'
                self.RES_MARKUP[message.from_user.id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
                resolutions = DLYouTube.all_resolutions(self.url[message.from_user.id])
                for resolution in resolutions:
                    self.RES_MARKUP[message.from_user.id].add(resolution)
                self.bot.send_message(message.from_user.id, text="Choose a resolution via menu".format(message.from_user),
                                       reply_markup=self.RES_MARKUP[message.from_user.id])
                self.bot.register_next_step_handler(message, self.choose_YT_resolution)
            
            case 'audio':
                SENDING_QUEUE.append(message.from_user.id)
                self.user_data[message.from_user.id]['video_or_audio'] = 'audio'
                self.YT[message.from_user.id] = DLYouTube(self.url[message.from_user.id], client=CLIENTS[len(SENDING_QUEUE)])
                self.download(message)
            
            case _:
                self.bot.send_message(message.from_user.id, text="Please, use the menu to choose an option")

    def choose_YT_resolution(self, message):
        self.stages[message.from_user.id] = 'choose res'
        self.YT[message.from_user.id] = DLYouTube(self.url[message.from_user.id], res = message.text, client = CLIENTS[len(SENDING_QUEUE)])
        self.download(message) 

    def download(self, message):
        if self.stages[message.from_user.id] == 'download':
            return
        
        self.stages[message.from_user.id] = 'download'
        self.user_data[message.from_user.id]['file_size'] = str(self.YT[message.from_user.id].file_size)

        if self.YT[message.from_user.id].file_size > self.YT[message.from_user.id].MAX_FILESIZE:
            self.bot.send_message(message.from_user.id, "The file weights more than 1.5GB and cannot be sent via Telegram!")
            return

        try:
            self.download_msg[message.from_user.id] = self.bot.send_message(message.from_user.id, "Downloading, Please stand by...")
            stop = types.KeyboardButton('stop downloading')
            self.STOP_MARKUP[message.from_user.id] = types.ReplyKeyboardMarkup(resize_keyboard=True)
            self.STOP_MARKUP[message.from_user.id].add(stop)
            self.stop_msg[message.from_user.id] = self.bot.send_message(message.from_user.id,text='If you want to emergency stop the downloading process, please, click the button'.format(message.from_user), 
                                  reply_markup=self.STOP_MARKUP[message.from_user.id]) 
            self.YT[message.from_user.id].execute(message = message, bot = self.bot)
            self.send(message)
        
        except ExtractError:
            pass

        except Exception as e: # Extract error doesnt inherit Exception
            self.bot.send_message(message.from_user.id, "Something went wrong! Try again with the correct download options")
            self.get_text_messages(message)
            print(e)

    def is_stop(self, message):
        if message.text != 'stop downloading':
            self.send(message)
            return 
        
        self.YT[message.from_user.id].stop = True
        self.user_data[message.from_user.id]['status'] = 'stop'
        self.user_data[message.from_user.id]['time_elapsed'] = (datetime.datetime.now()
                                                                 - self.user_data[message.from_user.id]['time_elapsed']).total_seconds()
        self.add_user_data(message)
        self.bot.send_message(message.from_user.id, 
                              "The data was erased successfully", 
                              reply_markup=types.ReplyKeyboardRemove())
        self.stages[message.from_user.id] = 'start'
        self.get_text_messages(message)

    def send(self, message):
        print('\n\nSESSION NUMBER = ', len(SENDING_QUEUE), "\n\n")
        try:
            self.user_data[message.from_user.id]['status'] = 'done'
            if self.YT[message.from_user.id].vid_resolution:
                self.file_id[message.from_user.id] = self.YT[message.from_user.id].file_id
                self.bot.send_video(message.from_user.id, video = self.file_id[message.from_user.id])
                self.bot.send_message(message.from_user.id, "Enjoy!!", reply_markup=types.ReplyKeyboardRemove())
            else:
                self.file_id[message.from_user.id] = self.YT[message.from_user.id].file_id
                self.bot.send_audio(message.from_user.id, audio = self.file_id[message.from_user.id])
                self.bot.send_message(message.from_user.id, "Enjoy!!", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            print(e)
            self.bot.send_message(message.from_user.id, "Something went wrong! Try again please!"
                                  , reply_markup=types.ReplyKeyboardRemove())
            self.user_data[message.from_user.id]['status'] = 'error'
        self.user_data[message.from_user.id]['time_elapsed'] = (datetime.datetime.now()
                                                                 - self.user_data[message.from_user.id]['time_elapsed']).total_seconds()
        self.add_user_data(message)
        self.stages[message.from_user.id] = 'start'
        self.get_text_messages(message)
    
    def add_user_data(self, message):
        self.bot.delete_message(chat_id = message.chat.id, message_id = self.stop_msg[message.from_user.id].message_id)
        self.bot.delete_message(chat_id = message.chat.id, message_id = self.download_msg[message.from_user.id].message_id)
        self.db = DataBase()
        self.db.add_data(self.user_data[message.from_user.id])
        try:
            del self.YT[message.from_user.id]
            del self.define_type_message[message.from_user.id]
            del self.VID_OR_AUD_MARKUP[message.from_user.id]
            del self.RES_MARKUP[message.from_user.id]
            del self.STOP_MARKUP[message.from_user.id]
            del self.user_data[message.from_user.id]
            del self.stages[message.from_user.id]
            del self.file_id[message.from_user.id]
            del self.url[message.from_user.id]
            SENDING_QUEUE.pop()
            print('the object was erased for peer', message.from_user.id, 'successfuly!')
        except Exception as e:
            print(e)

        self.db.close_conection()

    def start_pooling(self):
        self.bot.infinity_polling(timeout=100, long_polling_timeout = 100)   

if __name__ == '__main__':
    dl = DownloadBot()
    dl.start_pooling()