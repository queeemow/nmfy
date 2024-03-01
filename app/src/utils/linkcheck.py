import re
import enum
from pytube import YouTube

class LinkCheck(enum.Enum): 
    invalid = 0
    youtube = 1
    instagram = 2
    
    @staticmethod
    def which_link(message):
        try:
            YouTube(message.text).streams.first
            return LinkCheck.youtube
        except Exception as e:
            if len(re.findall('https://www.instagram.com/.+', str(message))) > 0:
                return LinkCheck.instagram
            else:
                return LinkCheck.invalid
            
print(LinkCheck.which_link('https://www.youtube.com/live/oWW5TLrrbNo?si=WfZwOe9VfN1mTAaJ'))