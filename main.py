import os
import sqlite3
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# --- تنظیمات دیتابیس (روی Volume یا پوشه جاری) ---
DB_DIR = "/myfiles"
DB_PATH = os.path.join(DB_DIR, "app.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            price TEXT NOT NULL,
            product TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- توابع کمکی ---
def get_setting(key: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else ""

def set_setting(key: str, value: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def send_telegram_request(method: str, payload: dict):
    token = get_setting("bot_token")
    if not token:
        return None
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=5)
        return res.json()
    except Exception as e:
        print(f"Error sending request to Telegram: {e}")
        return None

# --- قالب HTML همراه با Tailwind CSS (Dark Mode) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدیریت ربات تلگرام</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
      tailwind.config = {
        darkMode: 'class',
      }
    </script>
</head>
<body class="bg-gray-900 text-gray-100 min-h-screen p-4 sm:p-8 font-sans">
    <div class="max-w-3xl mx-auto bg-gray-800 rounded-xl shadow-2xl p-6 border border-gray-700">
        
        <!-- بخش تنظیمات ربات -->
        <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-700 pb-2">تنظیمات ربات</h2>
        
        {% if msg %}
        <div class="mb-4 p-3 bg-blue-900/50 border border-blue-500 rounded-lg text-blue-200 text-sm">
            {{ msg }}
        </div>
        {% endif %}

        <form action="/set-webhook" method="post" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">توکن ربات تلگرام</label>
                <input type="text" name="bot_token" value="{{ bot_token }}" dir="ltr" placeholder="123456789:ABCdef..." required
                       class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-left">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-300 mb-1">آدرس دامنه Railway</label>
                <input type="text" name="domain" value="{{ domain }}" dir="ltr" placeholder="your-app.up.railway.app" required
                       class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-left">
            </div>
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
                ست کردن وبهوک
            </button>
        </form>

        <hr class="my-8 border-gray-700">

        <!-- بخش مدیریت محصولات (CRUD) -->
        <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-700 pb-2">مدیریت محصولات</h2>
        
        <!-- فرم افزودن محصول -->
        <form action="/product/add" method="post" class="space-y-4 mb-8 bg-gray-850 p-4 rounded-lg border border-gray-700/50">
            <h3 class="text-md font-semibold text-gray-200 mb-2">افزودن محصول جدید</h3>
            <div>
                <label class="block text-xs font-medium text-gray-400 mb-1">عنوان (Title)</label>
                <input type="text" name="title" required placeholder="مثال: اکانت پرمیوم"
                       class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
                <label class="block text-xs font-medium text-gray-400 mb-1">قیمت (Price)</label>
                <input type="text" name="price" required placeholder="مثال: ۱۰۰,۰۰۰ تومان"
                       class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
                <label class="block text-xs font-medium text-gray-400 mb-1">توضیحات محصول (Product)</label>
                <textarea name="product" rows="2" required placeholder="توضیحات مربوط به محصول..."
                          class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"></textarea>
            </div>
            <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
                ذخیره محصول
            </button>
        </form>

        <!-- لیست محصولات -->
        <div class="overflow-x-auto">
            <table class="w-full text-right text-sm text-gray-300">
                <thead class="bg-gray-700 text-gray-200 uppercase text-xs">
                    <tr>
                        <th class="p-3">ID</th>
                        <th class="p-3">عنوان</th>
                        <th class="p-3">قیمت</th>
                        <th class="p-3">توضیحات</th>
                        <th class="p-3 text-center">عملیات</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-700">
                    {% for p in products %}
                    <tr class="hover:bg-gray-750">
                        <td class="p-3">{{ p.id }}</td>
                        <td class="p-3 font-medium text-white">{{ p.title }}</td>
                        <td class="p-3">{{ p.price }}</td>
                        <td class="p-3 truncate max-w-xs">{{ p.product }}</td>
                        <td class="p-3 text-center">
                            <form action="/product/delete/{{ p.id }}" method="post" onsubmit="return confirm('آیا از حذف مطمئن هستید؟')">
                                <button type="submit" class="bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-3 rounded transition duration-200">
                                    حذف
                                </button>
                            </form>
                        </td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="5" class="p-4 text-center text-gray-500">هیچ محصولی ثبت نشده است.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

    </div>
</body>
</html>
"""

def render_html(products, bot_token="", domain="", msg=""):
    # رندر ساده جایگزین‌ها در HTML
    html = HTML_TEMPLATE
    html = html.replace("{{ bot_token }}", bot_token)
    html = html.replace("{{ domain }}", domain)
    
    msg_block = f'<div class="mb-4 p-3 bg-blue-900/50 border border-blue-500 rounded-lg text-blue-200 text-sm">{msg}</div>' if msg else ''
    if "{% if msg %}" in html:
        start = html.find("{% if msg %}")
        end = html.find("{% endif %}") + len("{% endif %}")
        html = html[:start] + msg_block + html[end:]

    # ساخت ردیف‌های جدول
    rows = ""
    if products:
        for p in products:
            rows += f"""
            <tr class="hover:bg-gray-750 border-b border-gray-700">
                <td class="p-3">{p['id']}</td>
                <td class="p-3 font-medium text-white">{p['title']}</td>
                <td class="p-3">{p['price']}</td>
                <td class="p-3 truncate max-w-xs">{p['product']}</td>
                <td class="p-3 text-center">
                    <form action="/product/delete/{p['id']}" method="post" onsubmit="return confirm('آیا از حذف مطمئن هستید؟')">
                        <button type="submit" class="bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-3 rounded transition duration-200">
                            حذف
                        </button>
                    </form>
                </td>
            </tr>
            """
    else:
        rows = '<tr><td colspan="5" class="p-4 text-center text-gray-500">هیچ محصولی ثبت نشده است.</td></tr>'

    start_loop = html.find("{% for p in products %}")
    end_loop = html.find("{% endfor %}") + len("{% endfor %}")
    html = html[:start_loop] + rows + html[end_loop:]

    return html

# --- مسیرهای وب ---

@app.get("/", response_class=HTMLResponse)
def index(msg: str = ""):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    conn.close()
    
    bot_token = get_setting("bot_token")
    domain = get_setting("domain")
    
    return render_html(products, bot_token, domain, msg)

@app.post("/set-webhook")
def set_webhook(bot_token: str = Form(...), domain: str = Form(...)):
    bot_token = bot_token.strip()
    clean_domain = domain.strip().rstrip('/')
    if not clean_domain.startswith("http"):
        clean_domain = f"https://{clean_domain}"
        
    set_setting("bot_token", bot_token)
    set_setting("domain", clean_domain)
    
    webhook_url = f"{clean_domain}/webhook"
    res = send_telegram_request("setWebhook", {"url": webhook_url})
    
    status_msg = "وبهوک با موفقیت ست شد." if res and res.get("ok") else f"خطا در ست کردن وبهوک: {res}"
    return RedirectResponse(url=f"/?msg={status_msg}", status_code=303)

@app.post("/product/add")
def add_product(title: str = Form(...), price: str = Form(...), product: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (title, price, product) VALUES (?, ?, ?)", (title, price, product))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

@app.post("/product/delete/{product_id}")
def delete_product(product_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/", status_code=303)

# --- منطق ربات تلگرام (Webhook) ---

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    
    # پردازش پیام‌های دریافت شده
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text == "/start":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM products")
            products = cursor.fetchall()
            conn.close()
            
            # ساخت دکمه‌های شیشه‌ای
            keyboard = []
            for p in products:
                keyboard.append([{"text": p["title"], "callback_data": f"prod_{p['id']}"}])
            
            payload = {
                "chat_id": chat_id,
                "text": "خوش آمدید! لطفاً یک محصول را انتخاب کنید:",
                "reply_markup": {"inline_keyboard": keyboard}
            }
            send_telegram_request("sendMessage", payload)

    # پردازش کلیک روی دکمه‌های شیشه‌ای
    elif "callback_query" in data:
        query = data["callback_query"]
        chat_id = query["message"]["chat"]["id"]
        callback_data = query["data"]
        
        if callback_data.startswith("prod_"):
            prod_id = int(callback_data.split("_")[1])
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
            p = cursor.fetchone()
            conn.close()
            
            if p:
                text = f"📦 *{p['title']}*\n\n💰 قیمت: {p['price']}\n\n📝 توضیحات:\n{p['product']}"
                keyboard = [
                    [{"text": "🛒 خرید", "callback_data": f"buy_{p['id']}"}]
                ]
                payload = {
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "reply_markup": {"inline_keyboard": keyboard}
                }
                send_telegram_request("sendMessage", payload)
                
        elif callback_data.startswith("buy_"):
            payload = {
                "callback_query_id": query["id"],
                "text": "به زودی ...",
                "show_alert": True
            }
            send_telegram_request("answerCallbackQuery", payload)

    return {"status": "ok"}
