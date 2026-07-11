import streamlit as st
import streamlit.components.v1 as components
import time
import threading
import hashlib
import os
import json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import sqlite3
from datetime import datetime

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="X SUNNY E2E BY SYCO AHSAN",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# DATABASE FUNCTIONS (Built-in)
# ============================================
DB_PATH = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_config (
            user_id INTEGER PRIMARY KEY,
            chat_id TEXT DEFAULT '',
            name_prefix TEXT DEFAULT '',
            delay INTEGER DEFAULT 5,
            cookies TEXT DEFAULT '',
            messages TEXT DEFAULT '',
            automation_running BOOLEAN DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username already exists!"
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash)
    )
    user_id = cursor.lastrowid
    
    cursor.execute(
        "INSERT INTO user_config (user_id) VALUES (?)",
        (user_id,)
    )
    
    conn.commit()
    conn.close()
    return True, "User created successfully!"

def verify_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute(
        "SELECT user_id FROM users WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    user = cursor.fetchone()
    conn.close()
    return user['user_id'] if user else None

def get_username(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user['username'] if user else None

def get_user_config(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_config WHERE user_id = ?", (user_id,))
    config = cursor.fetchone()
    conn.close()
    return dict(config) if config else None

def update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_config 
        SET chat_id = ?, name_prefix = ?, delay = ?, cookies = ?, messages = ?
        WHERE user_id = ?
    ''', (chat_id, name_prefix, delay, cookies, messages, user_id))
    conn.commit()
    conn.close()

def set_automation_running(user_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE user_config SET automation_running = ? WHERE user_id = ?",
        (1 if status else 0, user_id)
    )
    conn.commit()
    conn.close()

def get_automation_running(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT automation_running FROM user_config WHERE user_id = ?",
        (user_id,)
    )
    result = cursor.fetchone()
    conn.close()
    return bool(result['automation_running']) if result else False

# Initialize database
init_db()

# ============================================
# CSS THEME - X SUNNY STYLE
# ============================================
custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Great+Vibes&family=Playfair+Display:wght@400;700&display=swap');

    * { font-family: 'Playfair Display', serif; }

    .stApp {
        background-image: linear-gradient(rgba(255, 165, 0, 0.15), rgba(255, 140, 0, 0.25)),
                          url('https://i.ibb.co/W44ZvkQj/Picsart-26-04-29-21-54-28-037.png');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    .main .block-container {
        background: rgba(255, 165, 0, 0.12);
        backdrop-filter: blur(15px);
        border-radius: 22px;
        padding: 32px;
        border: 2px solid rgba(255, 165, 0, 0.5);
        box-shadow: 0 12px 45px rgba(255, 165, 0, 0.25),
                    inset 0 0 28px rgba(255, 165, 0, 0.10);
    }

    .main-header {
        background: linear-gradient(135deg, #FF8C00, #FFA500, #FFD700, #FFA500, #FF8C00);
        border: 3px solid #FFD700;
        border-radius: 25px;
        padding: 2.4rem;
        text-align: center;
        margin-bottom: 2.8rem;
        box-shadow: 0 18px 55px rgba(255, 165, 0, 0.6),
                    0 0 50px rgba(255, 215, 0, 0.4);
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: "☀️";
        position: absolute;
        top: -30px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 7rem;
        opacity: 0.15;
        color: #FFD700;
    }

    .main-header h1 {
        background: linear-gradient(90deg, #8B0000, #FF4500, #FFD700, #FF4500, #8B0000);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Cinzel Decorative', cursive;
        font-size: 3.8rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 0 35px rgba(255, 165, 0, 0.8);
        animation: glow 2s ease-in-out infinite alternate;
    }

    @keyframes glow {
        from { text-shadow: 0 0 20px rgba(255, 165, 0, 0.6); }
        to { text-shadow: 0 0 40px rgba(255, 215, 0, 0.9), 0 0 60px rgba(255, 165, 0, 0.5); }
    }

    .main-header p {
        color: #8B0000;
        font-family: 'Great Vibes', cursive;
        font-size: 2rem;
        margin-top: 0.7rem;
        letter-spacing: 2px;
        text-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        font-weight: bold;
    }

    .sunny-text {
        color: #FFD700;
        text-shadow: 0 0 30px rgba(255, 165, 0, 0.8);
        font-size: 1.5rem;
        text-align: center;
        font-family: 'Great Vibes', cursive;
    }

    .prince-logo {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        margin-bottom: 22px;
        border: 4px solid #FFD700;
        box-shadow: 0 0 45px rgba(255, 215, 0, 0.9),
                    inset 0 0 25px rgba(255, 255, 255, 0.4);
        animation: spin 10s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .stButton>button {
        background: linear-gradient(45deg, #FF8C00, #FFA500, #FFD700, #FFA500);
        color: #4A0000;
        border: 2px solid #FFD700;
        border-radius: 16px;
        padding: 1rem 2.4rem;
        font-family: 'Cinzel Decorative', cursive;
        font-weight: 700;
        font-size: 1.2rem;
        transition: all 0.4s ease;
        box-shadow: 0 8px 30px rgba(255, 165, 0, 0.6);
        text-shadow: 1px 1px 3px rgba(255,255,255,0.3);
        width: 100%;
    }

    .stButton>button:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 15px 50px rgba(255, 165, 0, 0.9);
        background: linear-gradient(45deg, #FFD700, #FFA500, #FFD700);
    }

    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        background: rgba(255, 165, 0, 0.15);
        border: 2px solid #FF8C00;
        border-radius: 14px;
        color: #FFD700;
        padding: 1rem;
        font-size: 1.1rem;
    }

    .stTextInput>div>div>input::placeholder,
    .stTextArea>div>div>textarea::placeholder {
        color: #FFA500aa;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #FFD700;
        box-shadow: 0 0 0 4px rgba(255, 165, 0, 0.4);
        background: rgba(255, 165, 0, 0.25);
    }

    label {
        color: #FFD700 !important;
        font-weight: 600 !important;
        font-size: 1.15rem !important;
        text-shadow: 0 0 10px rgba(255, 165, 0, 0.5);
    }

    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 165, 0, 0.15);
        border-radius: 16px;
        padding: 10px;
        border: 1px solid #FF8C00;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 165, 0, 0.2);
        color: #FFD700;
        border-radius: 12px;
        padding: 14px 26px;
        font-weight: 600;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #FF8C00, #FFD700);
        color: #4A0000;
    }

    [data-testid="stMetricValue"] {
        color: #FFD700;
        font-size: 2.6rem;
        font-weight: 700;
        text-shadow: 0 0 25px rgba(255, 215, 0, 0.8);
    }

    [data-testid="stMetricLabel"] {
        color: #FFA500;
        font-weight: 500;
    }

    .console-output {
        background: rgba(50, 20, 0, 0.9);
        border: 2px solid #FF8C00;
        border-radius: 14px;
        padding: 18px;
        color: #FFD700;
        font-family: 'Courier New', monospace;
        font-size: 13.5px;
        max-height: 480px;
        overflow-y: auto;
    }

    .console-line {
        background: rgba(255, 165, 0, 0.1);
        border-left: 4px solid #FFD700;
        padding: 9px 14px;
        margin: 7px 0;
        color: #FFD700;
    }

    .footer {
        background: rgba(255, 165, 0, 0.15);
        border-top: 3px solid #FF8C00;
        color: #FFD700;
        font-family: 'Great Vibes', cursive;
        font-size: 1.8rem;
        padding: 2.8rem;
        text-shadow: 0 0 20px rgba(255, 165, 0, 0.5);
        text-align: center;
    }
    
    .sunny-badge {
        background: linear-gradient(45deg, #FF8C00, #FFD700);
        color: #4A0000;
        padding: 8px 20px;
        border-radius: 50px;
        display: inline-block;
        font-weight: bold;
        font-size: 1.2rem;
        box-shadow: 0 0 30px rgba(255, 165, 0, 0.5);
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ============================================
# SESSION STATE
# ============================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'automation_running' not in st.session_state:
    st.session_state.automation_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []
if 'message_count' not in st.session_state:
    st.session_state.message_count = 0
if 'auto_start_checked' not in st.session_state:
    st.session_state.auto_start_checked = False

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

if 'automation_state' not in st.session_state:
    st.session_state.automation_state = AutomationState()

# ============================================
# LOGGING FUNCTION
# ============================================
def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] ☀️ {msg}"
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        st.session_state.logs.append(formatted_msg)

# ============================================
# SELENIUM FUNCTIONS - UPDATED FOR STREAMLIT CLOUD
# ============================================
def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(10)
    
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
    
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        'div[aria-label*="Message" i][contenteditable="true"]',
        'div[contenteditable="true"][spellcheck="true"]',
        '[role="textbox"][contenteditable="true"]',
        'textarea[placeholder*="message" i]',
        'div[aria-placeholder*="message" i]',
        'div[data-placeholder*="message" i]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
    
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' ||
                               arguments[0].tagName === 'TEXTAREA' ||
                               arguments[0].tagName === 'INPUT';
                    """, element)
                    if is_editable:
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                        return element
                except Exception:
                    continue
        except Exception:
            continue
    return None

def setup_browser(automation_state=None):
    log_message('☀️ Setting up Chrome browser...', automation_state)
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
    
    # Try to find Chrome/Chromium on system
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
    
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            log_message(f'☀️ Found Chromium at: {chromium_path}', automation_state)
            break
    
    # Try to find ChromeDriver
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        '/usr/bin/chromium-driver'
    ]
    
    driver_path = None
    for driver_candidate in chromedriver_paths:
        if Path(driver_candidate).exists():
            driver_path = driver_candidate
            log_message(f'☀️ Found ChromeDriver at: {driver_path}', automation_state)
            break
    
    try:
        from selenium.webdriver.chrome.service import Service
        
        if driver_path:
            service = Service(executable_path=driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            log_message('☀️ Chrome started with detected ChromeDriver!', automation_state)
        else:
            # Try webdriver-manager if available
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver = webdriver.Chrome(
                    service=Service(ChromeDriverManager().install()),
                    options=chrome_options
                )
                log_message('☀️ Chrome started with webdriver-manager!', automation_state)
            except:
                # Fallback: try without specifying driver path
                driver = webdriver.Chrome(options=chrome_options)
                log_message('☀️ Chrome started with default driver!', automation_state)
        
        driver.set_window_size(1920, 1080)
        log_message('☀️ Chrome browser setup completed successfully!', automation_state)
        return driver
    except Exception as error:
        log_message(f'☀️ Browser setup failed: {error}', automation_state)
        raise error

def send_messages(config, automation_state, user_id, process_id='☀️ SUNNY-1'):
    driver = None
    try:
        log_message(f'{process_id}: ☀️ Starting automation...', automation_state)
        driver = setup_browser(automation_state)
        
        log_message(f'{process_id}: ☀️ Navigating to Facebook...', automation_state)
        driver.get('https://www.facebook.com/')
        time.sleep(8)
        
        if config['cookies'] and config['cookies'].strip():
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.facebook.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
        
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: ☀️ Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.facebook.com/messages/t/{chat_id}')
        else:
            log_message(f'{process_id}: ☀️ Opening messages...', automation_state)
            driver.get('https://www.facebook.com/messages')
        
        time.sleep(15)
        
        message_input = find_message_input(driver, process_id, automation_state)
        
        if not message_input:
            log_message(f'{process_id}: ☀️ Message input not found!', automation_state)
            automation_state.running = False
            set_automation_running(user_id, False)
            return 0
        
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
        
        if not messages_list:
            messages_list = ['Hello! ☀️']
        
        while automation_state.running:
            base_message = messages_list[automation_state.message_rotation_index % len(messages_list)]
            automation_state.message_rotation_index += 1
            
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
            
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                    
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                    
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                    
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                    element.dispatchEvent(new InputEvent('input', { bubbles: true, data: message }));
                """, message_input, message_to_send)
                
                time.sleep(1)
                
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
                
                if sent == 'button_not_found':
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        const events = [
                            new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keypress', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }),
                            new KeyboardEvent('keyup', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true })
                        ];
                        events.forEach(event => element.dispatchEvent(event));
                    """, message_input)
                
                messages_sent += 1
                automation_state.message_count = messages_sent
                log_message(f'{process_id}: ☀️ Message #{messages_sent} sent. Waiting {delay}s...', automation_state)
                time.sleep(delay)
                
            except Exception as e:
                log_message(f'{process_id}: ☀️ Send error: {str(e)[:100]}', automation_state)
                time.sleep(5)
        
        log_message(f'{process_id}: ☀️ Automation stopped. Total: {messages_sent}', automation_state)
        return messages_sent
        
    except Exception as e:
        log_message(f'{process_id}: ☀️ Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: ☀️ Browser closed', automation_state)
            except:
                pass

# ============================================
# AUTOMATION CONTROLS
# ============================================
def start_automation(user_config, user_id):
    automation_state = st.session_state.automation_state
    if automation_state.running:
        return
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    set_automation_running(user_id, True)
    username = get_username(user_id)
    thread = threading.Thread(target=send_messages, args=(user_config, automation_state, user_id))
    thread.daemon = True
    thread.start()

def stop_automation(user_id):
    st.session_state.automation_state.running = False
    set_automation_running(user_id, False)

# ============================================
# LOGIN PAGE
# ============================================
def login_page():
    st.markdown("""
    <div class="main-header">
        <img src="https://i.ibb.co/W44ZvkQj/Picsart-26-04-29-21-54-28-037.png" class="prince-logo">
        <h1>☀️ X SUNNY ☀️</h1>
        <p>E2E OFFLINE FACEBOOK AUTOMATION</p>
        <div class="sunny-badge">🌞 SYCO AHSAN PRESENTS 🌞</div>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["☀️ Login", "☀️ Sign Up"])
    
    with tab1:
        st.markdown("### Welcome Back! ☀️")
        username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        password = st.text_input("Password", key="login_password", type="password", placeholder="Enter your password")
        if st.button("☀️ Login", key="login_btn", use_container_width=True):
            if username and password:
                user_id = verify_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.success(f"☀️ Welcome back, {username}! ☀️")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password!")
            else:
                st.warning("⚠️ Please enter both username and password")
    
    with tab2:
        st.markdown("### Create New Account ☀️")
        new_username = st.text_input("Choose Username", key="signup_username", placeholder="Choose a unique username")
        new_password = st.text_input("Choose Password", key="signup_password", type="password", placeholder="Create a strong password")
        confirm_password = st.text_input("Confirm Password", key="confirm_password", type="password", placeholder="Re-enter your password")
        if st.button("☀️ Create Account", key="signup_btn", use_container_width=True):
            if new_username and new_password and confirm_password:
                if new_password == confirm_password:
                    success, message = create_user(new_username, new_password)
                    if success:
                        st.success(f"☀️ {message} Please login now! ☀️")
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Passwords do not match!")
            else:
                st.warning("⚠️ Please fill all fields")

# ============================================
# MAIN APP
# ============================================
def main_app():
    st.markdown("""
    <div class="main-header">
        <img src="https://i.ibb.co/W44ZvkQj/Picsart-26-04-29-21-54-28-037.png" class="prince-logo">
        <h1>☀️ X SUNNY ☀️</h1>
        <p>səvən bıllıon smıləs ın ʈhıs world buʈ ɣours ıs mɣ fαvourıʈəs___</p>
        <div class="sunny-badge">🌞 E2E OFFLINE AUTOMATION 🌞</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.auto_start_checked and st.session_state.user_id:
        st.session_state.auto_start_checked = True
        should_auto_start = get_automation_running(st.session_state.user_id)
        if should_auto_start and not st.session_state.automation_state.running:
            user_config = get_user_config(st.session_state.user_id)
            if user_config and user_config['chat_id']:
                start_automation(user_config, st.session_state.user_id)
    
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 10px;">
        <div style="font-size: 3rem;">☀️</div>
        <h3 style="color: #FFD700;">{st.session_state.username}</h3>
        <p style="color: #FFA500;">User ID: {st.session_state.user_id}</p>
        <div class="sunny-badge">✅ AUTOMATION READY</div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        if st.session_state.automation_state.running:
            stop_automation(st.session_state.user_id)
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.auto_start_checked = False
        st.rerun()
    
    user_config = get_user_config(st.session_state.user_id)
    
    if user_config:
        tab1, tab2 = st.tabs(["⚙️ Configuration", "🚀 Automation"])
        
        with tab1:
            st.markdown("### ☀️ Your Configuration")
            
            chat_id = st.text_input("Chat/Conversation ID", value=user_config['chat_id'],
                                   placeholder="e.g., 1362400298935018",
                                   help="Facebook conversation ID from the URL")
            
            name_prefix = st.text_input("Name Prefix", value=user_config['name_prefix'],
                                       placeholder="e.g., [X SUNNY]",
                                       help="Prefix to add before each message")
            
            delay = st.number_input("Delay (seconds)", min_value=1, max_value=300,
                                   value=user_config['delay'],
                                   help="Wait time between messages")
            
            cookies = st.text_area("Facebook Cookies (optional)", value="",
                                  placeholder="Paste your Facebook cookies here",
                                  height=100,
                                  help="Your cookies are encrypted and never shown to anyone")
            
            messages = st.text_area("Messages (one per line)", value=user_config['messages'],
                                   placeholder="Type your messages here...",
                                   height=150,
                                   help="Enter each message on a new line")
            
            if st.button("☀️ Save Configuration", use_container_width=True):
                final_cookies = cookies if cookies.strip() else user_config['cookies']
                update_user_config(
                    st.session_state.user_id,
                    chat_id,
                    name_prefix,
                    delay,
                    final_cookies,
                    messages
                )
                st.success("☀️ Configuration saved successfully! ☀️")
                st.rerun()
        
        with tab2:
            st.markdown("### ☀️ Automation Control")
            
            user_config = get_user_config(st.session_state.user_id)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📨 Messages Sent", st.session_state.automation_state.message_count)
            with col2:
                status = "🟢 Running" if st.session_state.automation_state.running else "🔴 Stopped"
                st.metric("📊 Status", status)
            with col3:
                st.metric("💬 Chat ID", user_config['chat_id'][:10] + "..." if user_config['chat_id'] else "Not Set")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Start Automation", disabled=st.session_state.automation_state.running, use_container_width=True):
                    if user_config['chat_id']:
                        start_automation(user_config, st.session_state.user_id)
                        st.success("☀️ Automation started! ☀️")
                        st.rerun()
                    else:
                        st.error("❌ Please set Chat ID in Configuration first!")
            
            with col2:
                if st.button("⏹️ Stop Automation", disabled=not st.session_state.automation_state.running, use_container_width=True):
                    stop_automation(st.session_state.user_id)
                    st.warning("☀️ Automation stopped! ☀️")
                    st.rerun()
            
            if st.session_state.automation_state.logs:
                st.markdown("### 📝 Live Console Output")
                
                logs_html = '<div class="console-output">'
                for log in st.session_state.automation_state.logs[-30:]:
                    logs_html += f'<div class="console-line">{log}</div>'
                logs_html += '</div>'
                
                st.markdown(logs_html, unsafe_allow_html=True)
                
                if st.button("🔄 Refresh Logs"):
                    st.rerun()
    else:
        st.warning("⚠️ No configuration found. Please refresh the page!")

# ============================================
# APP ROUTING
# ============================================
if not st.session_state.logged_in:
    login_page()
else:
    main_app()

st.markdown("""
<div class="footer">
    ☀️ Made by X SUNNY | SYCO AHSAN ☀️<br>
    <span style="font-size: 1rem; color: #FFA500;">© 2026 All Rights Reserved</span>
</div>
""", unsafe_allow_html=True)
