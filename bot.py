import telebot
import google.generativeai as genai
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(TELEGRAM_TOKEN)

SYSTEM_PROMPT = """Sen Biznes Miyasi — O'zbekistonning birinchi AI biznes maslahatchi botidir.
Sening vazifang: kichik va o'rta biznes egalariga moliyaviy maslahat berish.

Qoidalar:
- Faqat o'zbek tilida javob ber
- Aniq va qisqa javob ber
- Har doim 3 ta amaliy tavsiya ber
- Raqamlar bilan ishlashni yaxshi bilasan
- Do'stona va professional ohangda gapir
- Har javob oxirida Risk Skorini bel: Past/O'rta/Yuqori"""

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, """🧠 *BIZNES MIYASI ga xush kelibsiz!*

Men sizning AI biznes maslahatchingizman.

📊 Menga quyidagilarni so'rang:
• Xarajatlarim qanday kamaytiraman?
• Foydam nega tushib ketdi?
• Bankrotlik xavfim bormi?
• Narxni qanday belgilayman?

Savolingizni yozing! 👇""", parse_mode="Markdown")

@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, """💡 *Qanday foydalanish:*

Shunchaki savolingizni yozing:
• "Kafe ochmoqchiman, nima kerak?"
• "Oylik xarajatim 15 mln, daromadim 12 mln — nima qilay?"
• "Xodimlarim soni qancha bo'lishi kerak?"

📈 Men sizga real tavsiyalar beraman!""", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    user_text = message.text
    bot.send_chat_action(message.chat.id, "typing")
    
    try:
        prompt = f"{SYSTEM_PROMPT}\n\nFoydalanuvchi savoli: {user_text}"
        response = model.generate_content(prompt)
        answer = response.text
        
        if len(answer) > 4000:
            answer = answer[:4000] + "..."
            
        bot.reply_to(message, answer, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "⚠️ Xatolik yuz berdi. Iltimos qayta yuboring.")

bot.infinity_polling()
