import os
import math
from pytube import YouTube
from pytube.exceptions import ExtractError
from telethon.sync import TelegramClient
import asyncio
from hashlib import md5
from telethon.tl.functions.upload import SaveFilePartRequest, SaveBigFilePartRequest
from telethon.tl.types import InputFile, InputFileBig, DocumentAttributeVideo, DocumentAttributeAudio
from telethon.utils import pack_bot_file_id
from dotenv.main import load_dotenv
import ffmpeg
load_dotenv()

API_ID = os.environ['API_ID']
API_HASH = os.environ['API_HASH']

import time

class MsgId:
    last_time = 0
    offset = 0

    def __new__(cls) -> int:
        now = int(time.time())
        cls.offset = (cls.offset + 4) if now == cls.last_time else 0
        msg_id = (now * 2 ** 32) + cls.offset
        cls.last_time = now

        return msg_id

class DLYouTube:
    MAX_FILESIZE = 12901888884 
    path = None 
    url = None 
    stream = None 
    vid_resolution = None 
    file_name = None 
    file_size = None
    file_id = None
    file_total_parts = None
    file_part = None
    md5_sum = None
    file = None
    width = None
    height = None
    is_big = None
    stop = None
    progress = None
    access_hash = None
    user_id = None
    app = None
    bot = None
    message = None
    msg = None

    def __init__(self, url, res = None, client = 1) -> None: 
        try: 
            os.mkdir('data') 
        except:
            pass
        try: 
            os.mkdir('sessions') 
        except:
            pass
        self.path = os.path.abspath('data')
        self.sessions_path = os.path.abspath('sessions')
        self.url = url
        self.stream = YouTube(self.url, on_progress_callback=self.on_progress, on_complete_callback = self.on_complete)
        self.vid_resolution = res
        if self.vid_resolution == '360':
            self.file_size = self.stream.streams.get_by_resolution(self.vid_resolution+ 'p').filesize 
            self.file_name = fr'{self.stream.title.split()[0]}_{self.vid_resolution}.mp4'
            self.width = 640
            self.height = 360

        if self.vid_resolution == '720':
            self.file_size = self.stream.streams.get_by_resolution(self.vid_resolution+ 'p').filesize 
            self.file_name = fr'{self.stream.title.split()[0]}_{self.vid_resolution}.mp4'
            self.width = 1280
            self.height = 720

        if self.vid_resolution == None:
            self.file_size = self.stream.streams.get_by_itag(140).filesize 
            self.file_name = fr'{self.stream.title.split()[0]}.mp3'

        self.is_big = self.file_size > 10 * 1024 * 1024
        self.file_id = MsgId()
        self.md5_sum = md5()
        self.file_part = 0

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.app = TelegramClient(f'{self.sessions_path}/{client}.session', api_id=API_ID, api_hash=API_HASH)
        self.app.start()

    def __del__(self):
        self.app.disconnect()
        print('DLYouTube object was erased successfully!')

    def on_complete(self, *args):
        self.app.disconnect()
        self.bot.edit_message_text(text = '100' + '%', chat_id = self.message.chat.id, message_id = self.msg.message_id) 
        self.bot.delete_message(chat_id = self.message.chat.id, message_id = self.msg.message_id)

    def on_progress(self, stream, chunk: bytes, bytes_remaining: int):
        if self.stop:
            self.app.disconnect()
            print('STOP!!!!!!!!!!!!!! = ', self.stop)
            raise ExtractError
        
        self.file_size = stream.filesize
        self.file_total_parts = math.ceil(self.file_size/(512*1024))
        self.progress = self.file_part / self.file_total_parts * 100
        if self.progress >= 1:
            self.bot.edit_message_text(text = str(round(self.progress, 2)) + '%', chat_id = self.message.chat.id, message_id = self.msg.message_id)
        
        try: 
            self.app.loop.run_until_complete(self.send_part(chunk = chunk))
        except Exception as e:
            print(e)


    async def send_part(self, chunk = None):
        if self.is_big:
            await self.app(SaveBigFilePartRequest(file_id=self.file_id,
                                file_part=self.file_part,
                                file_total_parts=self.file_total_parts,
                                bytes=chunk))
        else:
            await self.app(SaveFilePartRequest(file_id=self.file_id,
                                file_part=self.file_part,
                                bytes=chunk))
        #deleting chunk as soon as it has been installed
        if (os.path.isfile(self.path+ '/'+ self.file_name)):
            os.remove(self.path+ '/'+ self.file_name)
        #if the chunk is the final one, calling the closing method InputFile and sending the whole file via second telegram account
        if len(chunk) < 512 * 1024:
            if self.is_big:
                self.file= InputFileBig(id=self.file_id,
                                        parts=self.file_total_parts,
                                        name=self.file_name)
            else:
                self.file= InputFile(id=self.file_id,
                                        parts=self.file_total_parts,
                                        name=self.file_name,
                                        md5_checksum='')
                
            if self.vid_resolution:
                doc = await self.app.send_file('@NMFY_BOT', file=self.file, attributes=[DocumentAttributeVideo(w = self.width,
                                                                                                           h = self.height,
                                                                                                            duration=self.stream.length)])
            else:
                doc = await self.app.send_file('@NMFY_BOT', file=self.file, attributes=[DocumentAttributeAudio(duration=self.stream.length)])
            self.file_id = pack_bot_file_id(doc.document)
        self.file_part += 1


    def execute(self,message = None,bot = None):
        self.message = message
        self.bot = bot
        self.msg = self.bot.send_message(self.message.from_user.id, '0' + '%')
        if self.vid_resolution == None:
            self.file_name = fr'{self.stream.title.split()[0]}.mp3'
            print('download method start')
            self.path = self.path + '/audios'
            self.stream.streams.get_by_itag(140).download(self.path, self.file_name)
            print('download method end')
        else:
            print('download method start')
            self.file_name = fr'{self.stream.title.split()[0]}_{self.vid_resolution}.mp4'
            print("filename = ", self.file_name)
            self.path = self.path + '/videos'
            print('STREAM = ', self.stream.streams.get_by_resolution(self.vid_resolution))
            self.stream.streams.get_by_resolution(self.vid_resolution + 'p').download(self.path, self.file_name)
            print("Download method end")

    @staticmethod
    def all_resolutions(url):
        available_resolutions = []
        for v in YouTube(url).streams.filter(only_audio=False, file_extension = 'mp4', progressive=True):
            try:
                available_resolutions.append(str(v).split()[3][5:8])
            except Exception as e:
                print(e)
                break
            available_resolutions = sorted(set(available_resolutions))
        return available_resolutions

