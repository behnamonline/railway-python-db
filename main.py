import os
import sqlite3
import requests
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

# --- تنظیمات دیتابیس (بررسی و ساخت پوشه /myfiles) ---
DB_DIR = "/dbfiles"
if DB_DIR == "/dbfiles":
    os.makedirs(DB_DIR, exist_ok=True)

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

# --- مسیرهای وب ---

@app.get("/", response_class=HTMLResponse)
def index(msg: str = "", edit: int = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products ORDER BY id DESC")
    products = cursor.fetchall()
    
    edit_item = None
    if edit:
        cursor.execute("SELECT * FROM products WHERE id = ?", (edit,))
        edit_item = cursor.fetchone()
        
    conn.close()
    
    bot_token = get_setting("bot_token")
    
    # مقادیر پیش‌فرض فرم (در حالت افزودن)
    form_action = "/product/add"
    form_title = "افزودن محصول جدید"
    btn_text = "ذخیره محصول"
    edit_id = ""
    title_val = ""
    price_val = ""
    product_val = ""
    cancel_btn = ""

    # مقادیر فرم در صورت ویرایش
    if edit_item:
        form_action = f"/product/edit/{edit_item['id']}"
        form_title = "ویرایش محصول"
        btn_text = "بروزرسانی محصول"
        edit_id = edit_item["id"]
        title_val = edit_item["title"]
        price_val = edit_item["price"]
        product_val = edit_item["product"]
        cancel_btn = '<a href="/" class="bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg text-sm inline-block mr-2">انصراف</a>'

    # پیام سیستم
    msg_html = f'<div class="mb-4 p-3 bg-blue-900/50 border border-blue-500 rounded-lg text-blue-200 text-sm">{msg}</div>' if msg else ''

    # رندر لیست محصولات
    product_rows = ""
    for p in products:
        product_rows += f"""
        <tr class="hover:bg-gray-750 border-b border-gray-700">
            <td class="p-3 text-center">{p['id']}</td>
            <td class="p-3 font-medium text-white">{p['title']}</td>
            <td class="p-3">{p['price']}</td>
            <td class="p-3">{p['product']}</td>
            <td class="p-3 text-center">
                <div class="flex justify-center gap-2">
                    <a href="/?edit={p['id']}" class="bg-yellow-600 hover:bg-yellow-700 text-white text-xs py-1 px-3 rounded">ویرایش</a>
                    <form action="/product/delete/{p['id']}" method="post" onsubmit="return confirm('آیا از حذف این محصول اطمینان دارید؟')">
                        <button type="submit" class="bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-3 rounded">حذف</button>
                    </form>
                </div>
            </td>
        </tr>
        """

    if not products:
        product_rows = '<tr><td colspan="5" class="p-4 text-center text-gray-500">هیچ محصولی یافت نشد.</td></tr>'

    # قالب کامل HTML با پدینگ مناسب در body (pb-32)
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fa" dir="rtl" class="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>مدیریت ربات تلگرام</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script>
          tailwind.config = {{
            darkMode: 'class',
          }}
        </script>
    </head>
    <body class="bg-gray-900 text-gray-100 min-h-screen p-4 sm:p-8 pb-32 font-sans" style="padding-bottom:90vh">
        <div class="max-w-3xl mx-auto bg-gray-800 rounded-xl shadow-2xl p-6 border border-gray-700">
            
            <!-- تنظیمات ربات -->
            <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-700 pb-2">تنظیمات ربات</h2>
            {msg_html}
            <form action="/set-webhook" method="post" class="space-y-4 mb-8">
                <div>
                    <label class="block text-sm font-medium text-gray-300 mb-1">توکن ربات تلگرام</label>
                    <input type="text" name="bot_token" value="{bot_token}" dir="ltr" placeholder="123456789:ABCdef..." required
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 text-left">
                </div>
                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
                    ست کردن وبهوک
                </button>
            </form>

            <hr class="my-8 border-gray-700">

            <!-- مدیریت محصولات -->
            <h2 class="text-xl font-bold mb-4 text-blue-400 border-b border-gray-700 pb-2">مدیریت محصولات</h2>
            
            <!-- فرم افزودن/ویرایش -->
            <form action="{form_action}" method="post" class="space-y-4 mb-8 bg-gray-900/50 p-4 rounded-lg border border-gray-700">
                <h3 class="text-md font-semibold text-gray-200">{form_title}</h3>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">عنوان (Title)</label>
                    <input type="text" name="title" value="{title_val}" required placeholder="مثال: اکانت پرمیوم"
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">قیمت (Price)</label>
                    <input type="text" name="price" value="{price_val}" required placeholder="مثال: ۱۰۰,۰۰۰ تومان"
                           class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                </div>
                <div>
                    <label class="block text-xs font-medium text-gray-400 mb-1">توضیحات محصول (Product)</label>
                    <textarea name="product" rows="3" required placeholder="توضیحات مربوط به محصول..."
                              class="w-full bg-gray-700 border border-gray-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">{product_val}</textarea>
                </div>
                <div>
                    <button type="submit" class="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition duration-200">
                        {btn_text}
                    </button>
                    {cancel_btn}
                </div>
            </form>

            <!-- جدول نمایش محصولات -->
            <div class="overflow-x-auto rounded-lg border border-gray-700">
                <table class="w-full text-right text-sm text-gray-300">
                    <thead class="bg-gray-700 text-gray-200 uppercase text-xs">
                        <tr>
                            <th class="p-3 text-center">ID</th>
                            <th class="p-3">عنوان</th>
                            <th class="p-3">قیمت</th>
                            <th class="p-3">توضیحات</th>
                            <th class="p-3 text-center">عملیات</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-700 bg-gray-800">
                        {product_rows}
                    </tbody>
                </table>
            </div>

        </div>
    </body>
    </html>
    """
    return html_content

@app.post("/set-webhook")
def set_webhook(request: Request, bot_token: str = Form(...)):
    bot_token = bot_token.strip()
    
    scheme = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("host", request.base_url.netloc)
    domain = f"https://{host}"
    
    set_setting("bot_token", bot_token)
    set_setting("domain", domain)
    
    webhook_url = f"{domain}/webhook"
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

@app.post("/product/edit/{product_id}")
def update_product(product_id: int, title: str = Form(...), price: str = Form(...), product: str = Form(...)):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET title = ?, price = ?, product = ? WHERE id = ?", (title, price, product, product_id))
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
    
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        
        if text == "/start":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM products")
            products = cursor.fetchall()
            conn.close()
            
            keyboard = []
            for p in products:
                keyboard.append([{"text": p["title"], "callback_data": f"prod_{p['id']}"}])
            
            payload = {
                "chat_id": chat_id,
                "text": "خوش آمدید! لطفاً یک محصول را انتخاب کنید:",
                "reply_markup": {"inline_keyboard": keyboard}
            }
            send_telegram_request("sendMessage", payload)

    elif "callback_query" in data:
        query = data["callback_query"]
        query_id = query["id"]
        chat_id = query["message"]["chat"]["id"]
        callback_data = query["data"]
        
        if callback_data.startswith("prod_"):
            send_telegram_request("answerCallbackQuery", {"callback_query_id": query_id})
            
            prod_id = int(callback_data.split("_")[1])
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ?", (prod_id,))
            p = cursor.fetchone()
            conn.close()
            
            if p:
                caption = f"📦 *{p['title']}*\n\n💰 قیمت: {p['price']}\n\n📝 توضیحات:\n{p['product']}"
                keyboard = [
                    [{"text": "🛒 خرید", "callback_data": f"buy_{p['id']}"}]
                ]
                payload = {
                    "chat_id": chat_id,
                    "text": caption,
                    "parse_mode": "Markdown",
                    "reply_markup": {"inline_keyboard": keyboard}
                }
                send_telegram_request("sendMessage", payload)
                
        elif callback_data.startswith("buy_"):
            payload = {
                "callback_query_id": query_id,
                "text": "به زودی ...",
                "show_alert": True
            }
            send_telegram_request("answerCallbackQuery", payload)

    return {"status": "ok"}
