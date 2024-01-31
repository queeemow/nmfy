import re
import enum

class LinkCheck(enum.Enum): 
    invalid = 0
    youtube = 1
    instagram = 2
    
    @staticmethod
    def which_link(message):
        if len(re.findall('youtu.+', str(message))) > 0:
            return LinkCheck.youtube
        if len(re.findall('https://www.instagram.com/.+', str(message))) > 0:
            return LinkCheck.instagram
        else:
            return LinkCheck.invalid