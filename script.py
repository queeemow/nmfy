import shutil
import os

print(os.path.abspath('2.session'))

shutil.copyfile('/Users/glebkuimov/Desktop/nmfy_bot/sessions/2.session', '/Users/glebkuimov/Desktop/nmfy_bot/sessions/3.session')
for i in range(3,100):
    shutil.copyfile('/Users/glebkuimov/Desktop/nmfy_bot/sessions/2.session', f'/Users/glebkuimov/Desktop/nmfy_bot/sessions/{i}.session')
