import telebot
import os
import re
import random
import time
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import threading
from flask import Flask
from telebot.apihelper import ApiTelegramException
from pymongo import MongoClient
import html

# FIXED: Set your actual bot token here first
TOKEN = ""  # Replace with token from @BotFather

# MongoDB URI (fixed warning)
MONGOURI = "mongodb+srv://editingtution99:kLKimOFEX1MN1v0G@cluster0.fxbujjd.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
OWNER = 8458169280

# Initialize bot FIRST
if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("❌ ERROR: Set your bot token in TOKEN variable!")
    print("Get token from @BotFather -> /newbot")
    exit(1)

print("✅ Initializing bot...")
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()
print("✅ Bot initialized successfully!")

# MongoDB
client = MongoClient(MONGOURI)
db = client['sujalbot']
usercollection = db['sujalbot']
userstate = {}
app = Flask(__name__)

blockedusers = set()


def safesend(sendfn, *args, **kwargs):
    chatid = args[0] if args else kwargs.get('chat_id')
    try:
        return sendfn(*args, **kwargs)
    except ApiTelegramException as e:
        if "bot was blocked by the user" in str(e):
            blockedusers.add(chatid)
            print(f"User {chatid} blocked the bot.")
        else:
            print(f"Error for chatid {chatid}: {e}")
    except Exception as e:
        print(f"safesend error: {e}")
    return None

blockedusers = set()

def txttohtml(txtpath, htmlpath):
    filename = os.path.basename(txtpath).replace('.txt', '')
    
    with open(txtpath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    
    sections = {'video': {}, 'pdf': {}, 'other': {}}
    
    def categorizelink(name, url):
        if re.search(r'\.mp4|\.mkv|\.avi|\.mov|\.flv|\.wmv|\.m3u8', url, re.IGNORECASE) or 'brightcove' in url:
            return 'video'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif re.search(r'\.pdf', url, re.IGNORECASE):
            return 'pdf'
        else:
            return 'other'
    
    def extracttopic(name):
        match = re.search(r'\[(.+?)\]', name)
        if match: return match.group(1).strip()
        parts = name.split('|')
        if parts: return parts[0].strip()
        return 'Misc'
    
    for line in lines:
        line = line.strip()
        if not line: continue
        match = re.match(r'^(.*?)\s+https?://', line)
        if match:
            name, url = match.groups()
            name, url = name.strip(), url.strip()
            category = categorizelink(name, url)
            topic = extracttopic(name)
            sec = 'video' if category == 'youtube' else category
            if topic not in sections[sec]:
                sections[sec][topic] = []
            sections[sec][topic].append((name, url, category))
    
    # Exact CSS from sample HTML
    css = '''
    <style>
    :root {
        --bg-color: #121212; --text-color: #e8e8e8; --primary-color: #1e88e5;
        --secondary-color: #26a69a; --success-color: #43a047; --warning-color: #ff9800;
        --card-bg: #1e1e1e; --section-bg: #2a2a2a; --link-color: #42a5f5;
        --pdf-color: #ff7043; --image-color: #26c6da; --video-color: #ff3d71;
        --button-text: #ffffff;
        --gradient-primary: linear-gradient(135deg, #1e88e5 0%, #1976d2 100%);
        --gradient-secondary: linear-gradient(135deg, #26a69a 0%, #00695c 100%);
        --gradient-thumbnail: linear-gradient(135deg, #26c6da 0%, #0097a7 100%);
        --gradient-video: linear-gradient(135deg, #ff3d71 0%, #c2185b 100%);
        --shadow-glow: 0 4px 20px rgba(30, 136, 229, 0.25);
        --border-color: #333333;
    }
    [data-theme="light"] {
        --bg-color: #f8f9ff; --text-color: #2d3748; --primary-color: #0066cc;
        --secondary-color: #e67e22; --success-color: #27ae60; --warning-color: #f39c12;
        --card-bg: #ffffff; --section-bg: #e9ecef; --link-color: #0066cc;
        --pdf-color: #e67e22; --image-color: #16a085; --video-color: #e91e63;
        --gradient-primary: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        --gradient-secondary: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        --gradient-thumbnail: linear-gradient(135deg, #16a085 0%, #f4d03f 100%);
        --gradient-video: linear-gradient(135deg, #e91e63 0%, #ad1457 100%);
        --shadow-glow: 0 4px 20px rgba(0, 102, 204, 0.2);
        --border-color: #e2e8f0;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', Segoe UI, system-ui, sans-serif; background: var(--bg-color);
           color: var(--text-color); padding: 16px; margin: 0; transition: all 0.3s;
           line-height: 1.5; min-height: 100vh; }
    h1 { background: var(--gradient-primary); -webkit-background-clip: text;
         -webkit-text-fill-color: transparent; background-clip: text; text-align: center;
         font-size: clamp(1.6rem, 4vw, 2.5rem); font-weight: 800; margin: 12px 0 6px;
         text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); letter-spacing: -0.5px; }
    .conversion-info { text-align: center; margin: 4px 0 12px; font-size: 0.85rem; opacity: 0.8; }
    .meta-info { background: var(--card-bg); border: 1px solid var(--border-color);
                  border-radius: 10px; padding: 14px; margin: 8px auto 20px; max-width: 380px;
                  text-align: center; color: var(--text-color); font-size: 0.95rem;
                  font-weight: 600; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); }
    .total-links { background: var(--gradient-primary); -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent; font-weight: 700; font-size: 1.1rem; }
    .section-button { display: block; width: 100%; padding: 14px 20px; margin: 14px 0;
                      font-size: 1rem; font-weight: 600; text-align: center; color: var(--button-text);
                      background: var(--gradient-primary); border: none; border-radius: 10px;
                      cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                      box-shadow: var(--shadow-glow); position: relative; overflow: hidden; }
    .section-button::before { content: ''; position: absolute; top: 0; left: -100%; width: 100%;
                              height: 100%; background: linear-gradient(90deg, transparent,
                              rgba(255, 255, 255, 0.2), transparent); transition: left 0.5s ease; }
    .section-button:hover { transform: translateY(-3px) scale(1.02);
                            box-shadow: 0 6px 25px rgba(30, 136, 229, 0.4); }
    .section-button:hover::before { left: 100%; }
    .section { display: none; margin-bottom: 20px; animation: fadeInUp 0.4s ease; }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); }
                          to { opacity: 1; transform: translateY(0); } }
    .topic-button { background: var(--gradient-secondary); font-size: 0.95rem;
                    padding: 11px 18px; box-shadow: 0 4px 20px rgba(38, 166, 154, 0.25); }
    .topic-button:hover { box-shadow: 0 6px 25px rgba(38, 166, 154, 0.4); }
    ul { list-style-type: none; padding: 0; margin: 0; }
    li { background: var(--card-bg); margin: 10px 0; padding: 14px 16px; border-radius: 10px;
         box-shadow: 0 3px 12px rgba(0, 0, 0, 0.15); font-size: 0.95rem;
         transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); display: flex;
         justify-content: space-between; align-items: center; flex-wrap: wrap;
         border: 1px solid var(--border-color); }
    li:hover { transform: translateY(-3px) scale(1.01); box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
               border-color: var(--primary-color); background: var(--section-bg); }
    .number { font-weight: 700; color: var(--secondary-color); margin-right: 10px;
              min-width: 26px; font-size: 1rem; }
    .link-title { color: var(--link-color); text-decoration: none; flex-grow: 1;
                  word-break: break-word; font-weight: 500; font-size: 0.95rem;
                  transition: all 0.3s ease; }
    .link-title:hover { text-decoration: underline; color: var(--primary-color); }
    .video-title { color: var(--video-color); }
    .pdf-title { color: var(--pdf-color); }
    .image-title { color: var(--image-color); }
    .link-controls { display: flex; align-items: center; gap: 8px; margin-left: 8px; }
    .video-play-button { background: var(--gradient-video); color: var(--button-text);
                         border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer;
                         font-size: 0.85rem; font-weight: 600; margin-left: 8px;
                         transition: all 0.3s ease; box-shadow: 0 2px 8px rgba(255, 61, 113, 0.3); }
    .video-play-button:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(255, 61, 113, 0.5); }
    .popup-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                     background: rgba(0, 0, 0, 0.8); z-index: 1000; }
    .popup-content { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                     background: var(--card-bg); border-radius: 12px; width: 90%; max-width: 900px;
                     height: 80%; max-height: 600px; box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5); }
    .popup-header { display: flex; justify-content: space-between; align-items: center;
                    padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
    .popup-title { color: var(--text-color); font-weight: 600; font-size: 1.1rem; }
    .close-button { background: none; border: none; color: var(--text-color); font-size: 1.5rem;
                    cursor: pointer; padding: 4px 8px; border-radius: 4px; transition: background 0.3s ease; }
    .close-button:hover { background: var(--section-bg); }
    .video-container { width: 100%; height: calc(100% - 60px); padding: 0; }
    .video-frame { width: 100%; height: 100%; border: none; border-bottom-left-radius: 12px;
                   border-bottom-right-radius: 12px; }
    .controls { display: flex; justify-content: center; gap: 10px; margin-bottom: 25px;
                flex-wrap: wrap; }
    .theme-toggle { padding: 10px 20px; background: var(--gradient-primary); border: none;
                    border-radius: 8px; cursor: pointer; color: var(--button-text); font-size: 0.95rem;
                    font-weight: 600; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    box-shadow: var(--shadow-glow); }
    .theme-toggle:hover { transform: translateY(-2px) scale(1.05);
                          box-shadow: 0 6px 20px rgba(30, 136, 229, 0.4); }
    @media (max-width: 768px) {
        body { padding: 12px; }
        .controls { flex-direction: column; align-items: stretch; }
        .theme-toggle { width: 100%; margin-bottom: 10px; }
        li { flex-direction: column; align-items: flex-start; gap: 8px; }
        .number { margin-bottom: 4px; }
    }
    </style>
    '''
    
    htmlblocks = []
    for key in ['video', 'pdf', 'other']:
        topicblocks = []
        for tidx, (topic, items) in enumerate(sections[key].items()):
            links = []
            for cidx, (name, url, category) in enumerate(items):
                safename = html.escape(name)
                marshmallow_url = f"https://player.marshmallowapi.workers.dev?video={url}&title={name.replace(' ', '%20').replace('|', '%7C')}"
                
                links.append(f'''
                <li>
                    <span class="number">{cidx+1}.</span>
                    <a href="javascript:void(0)" class="link-title video-title" 
                       onclick="openVideoPopup('{marshmallow_url}', '{safename}')">{safename}</a>
                    <div class="link-controls">
                        <button class="video-play-button" onclick="openVideoPopup('{marshmallow_url}', '{safename}')">
                            <i class="fas fa-play"></i> Play</button>
                        <a href="{url}" target="_blank" style="margin-left: 8px; color: var(--link-color); text-decoration: none; font-size: 0.8rem;">Original</a>
                    </div>
                </li>''')
            
            topicblocks.append(f'''
            <button class="section-button topic-button" onclick="toggleSection('classes{key}{tidx}')">
                <i class="fas fa-folder"></i> {html.escape(topic)} ({len(items)})</button>
            <div id="classes{key}{tidx}" class="section">
                <ul>{''.join(links)}</ul>
            </div>''')
        
        htmlblocks.append(f'<div class="tab-content" id="{key}" style="display: none;">{''.join(topicblocks) if topicblocks else "<p>No content found</p>"}</div>')
    
    htmlcontent = f'''<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{html.escape(filename)}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        {css}
    </head>
    <body data-theme="dark">
        <h1>{html.escape(filename)}</h1>
        <div class="conversion-info">
            <div><i class="fas fa-magic"></i> Converted by Telegram Bot</div>
            <div><i class="fas fa-clock"></i> {time.strftime("%Y-%m-%d at %H:%M:%S")}</div>
        </div>
        <div class="meta-info">
            <div class="total-links">
                <i class="fas fa-link"></i> Total links: {sum(len(v) for v in sections['video'].values() + sections['pdf'].values() + sections['other'].values())}
            </div>
        </div>
        <div class="controls">
            <button class="section-button" onclick="showSection('video')"><i class="fas fa-video"></i> Classes ({sum(len(v) for v in sections['video'].values())})</button>
            <button class="section-button" onclick="showSection('pdf')"><i class="fas fa-file-pdf"></i> PDFs ({sum(len(v) for v in sections['pdf'].values())})</button>
            <button class="section-button" onclick="showSection('other')"><i class="fas fa-link"></i> Other ({sum(len(v) for v in sections['other'].values())})</button>
            <button class="theme-toggle" onclick="toggleTheme()"><i class="fas fa-palette"></i> Toggle Theme</button>
        </div>
        {''.join(htmlblocks)}
        <div id="videoPopup" class="popup-overlay" onclick="closeVideoPopup(event)">
            <div class="popup-content" onclick="event.stopPropagation()">
                <div class="popup-header">
                    <span class="popup-title" id="popupTitle">Video Player</span>
                    <button class="close-button" onclick="closeVideoPopup()">&times;</button>
                </div>
                <div class="video-container">
                    <iframe id="videoFrame" class="video-frame" allowfullscreen></iframe>
                </div>
            </div>
        </div>
        <script>
        function toggleSection(id) {{
            const section = document.getElementById(id);
            section.style.display = section.style.display === 'block' ? 'none' : 'block';
        }}
        function showSection(tabId) {{
            const tabs = document.querySelectorAll('.tab-content');
            tabs.forEach(tab => tab.style.display = 'none');
            document.getElementById(tabId).style.display = 'block';
        }}
        function toggleTheme() {{
            const body = document.body;
            if (body.getAttribute('data-theme') === 'dark') {{
                body.setAttribute('data-theme', 'light');
            }} else {{
                body.setAttribute('data-theme', 'dark');
            }}
        }}
        function openVideoPopup(videoUrl, title) {{
            document.getElementById('popupTitle').textContent = title;
            document.getElementById('videoFrame').src = videoUrl;
            document.getElementById('videoPopup').style.display = 'block';
            document.body.style.overflow = 'hidden';
        }}
        function closeVideoPopup(event) {{
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('videoPopup').style.display = 'none';
            document.getElementById('videoFrame').src = '';
            document.body.style.overflow = 'auto';
        }}
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') closeVideoPopup();
        }});
        document.addEventListener('DOMContentLoaded', function() {{
            showSection('video');
        }});
        </script>
    </body>
    </html>'''
    
    with open(htmlpath, 'w', encoding='utf-8') as f:
        f.write(htmlcontent)
    
    return (sum(len(v) for v in sections['video'].values()),
            sum(len(v) for v in sections['pdf'].values()),
            sum(len(v) for v in sections['other'].values()))

def startkeyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("📱 Telegram", url="https://t.me/sujalbot"),
                 InlineKeyboardButton("💬 Support", url="https://t.me/sujalbot"))
    return keyboard

@bot.message_handler(commands=['info'])
def info(message: Message):
    text = f"""**Your Telegram Info**
**Name**: {message.from_user.firstname} {message.from_user.lastname or ''}
**User ID**: @{message.from_user.username or 'NA'}
**TG ID**: `{message.from_user.id}`"""
    safesend(bot.send_message, message.chat.id, text=text, parse_mode='Markdown',
             disable_web_page_preview=True, reply_markup=startkeyboard())

REACTIONS = ['👍', '🔥', '❤️', '⭐', '👏', '🎉', '✨', '💯', '🚀', '😍']

@bot.message_handler(commands=['start'])
def startcommand(message: Message):
    userstate.pop(message.chat.id, None)
    userid = message.from_user.id
    mention = f"{message.from_user.firstname}"
    
    if not usercollection.find_one({'id': userid}):
        usercollection.insert_one({'id': userid})
    
    try:
        bot.set_message_reaction(chat_id=message.chat.id, message_id=message.message_id,
                               reaction=[{'type': 'emoji', 'emoji': random.choice(REACTIONS)}])
    except Exception as e:
        print(f"Reaction error: {e}")
    
    randomimageurl = random.choice([
        "https://envs.sh/Qt9.jpg",  # IMG20250621443.jpg
        "https://envs.sh/Fio.jpg",  # IMG2025070370.jpg
        "https://envs.sh/Fir.jpg"   # IMG20250703829.jpg
    ])
    caption = f"**{mention}** 👋\n\nI am a *Txt To HTML Converter Bot*\n\nUse `/html` to convert a `.txt` file to `.html` ✨"
    safesend(bot.send_photo, message.chat.id, photo=randomimageurl, caption=caption,
             parse_mode='Markdown', reply_markup=startkeyboard())

@bot.message_handler(commands=['broadcast'])
def broadcasthandler(message):
    if message.from_user.id != OWNER:
        return bot.reply_to(message, "You are not authorized to use broadcast.")
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return bot.reply_to(message, "Usage: `/broadcast Your message here`", parse_mode='Markdown')
    text = parts[1]
    success = failed = 0
    for user in usercollection.find():
        try:
            bot.send_message(user['id'], text, parse_mode='HTML', disable_web_page_preview=True)
            success += 1
        except Exception as e:
            failed += 1
            print(f"Failed to send to {user['id']}: {e}")
    bot.reply_to(message, f"""**Broadcast Summary**
**Sent**: `{success}`
**Failed**: `{failed}`""", parse_mode='Markdown')

@bot.message_handler(commands=['html'])
def askforfile(message):
    userstate[message.chat.id] = 'awaiting_txt'
    uid = message.chat.id
    if not usercollection.find_one({'id': uid}):
        usercollection.insert_one({'id': uid})
    bot.send_message(uid, """**Hii** 🖐️, I am *TXT TO Html bot* 📄✨

> Send me your `.txt` file to convert it to HTML""", parse_mode='HTML')

@bot.message_handler(content_types=['document'])
def handletxtfile(message: Message):
    if userstate.get(message.chat.id) != 'awaiting_txt':
        return userstate.pop(message.chat.id, None)
    
    try:
        fileid = message.document.file_id
        fileinfo = bot.get_file(fileid)
        originalfilename = message.document.filename
        
        if not originalfilename.endswith('.txt'):
            safesend(bot.send_message, message.chat.id, "Please send a valid `.txt` file.")
            return
        
        waitmsg = safesend(bot.send_message, message.chat.id,
                          "> Your HTML file is being generated, please wait... ⏳", parse_mode='HTML')
        
        filebase = os.path.splitext(originalfilename)[0].replace(' ', '_')
        txtpath = f"{filebase}.txt"
        htmlpath = f"{filebase}.html"
        
        downloaded = bot.download_file(fileinfo.file_path)
        with open(txtpath, 'wb') as f:
            f.write(downloaded)
        
        with open(txtpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        os.remove(txtpath)
        
        with open(txtpath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        videocount, pdfcount, othercount = txttohtml(txtpath, htmlpath)
        captiontext = f"📊 **{videocount}** Videos | **{pdfcount}** PDFs | **{othercount}** Others"
        
        with open(htmlpath, 'rb') as htmlfile, open(txtpath, 'rb') as txtfile:
            safesend(bot.send_document, message.chat.id, htmlfile, caption=captiontext, parse_mode='Markdown')
        
        if waitmsg:
            safesend(bot.delete_message, message.chat.id, waitmsg.message_id)
        
        # Send to channel
        txtfile.seek(0)
        safesend(bot.send_document, -1003014595955, txtfile, parse_mode='Markdown')
        htmlfile.seek(0)
        safesend(bot.send_document, -1003014595955, htmlfile,
                caption=f"**New TXT → HTML Received** 🎉\n**From**: {message.from_user.firstname}\n**File**: {originalfilename}", parse_mode='Markdown')
        
        os.remove(txtpath)
        os.remove(htmlpath)
        
    except Exception as e:
        safesend(bot.send_message, message.chat.id, "An error occurred while processing your file. ❌")
        print(f"Error: {e}")

if __name__ == '__main__':
    threading.Thread(target=renderweb.runflask).start()
    print("Bot is running... Waiting for messages.")
    bot.infinity_polling()
