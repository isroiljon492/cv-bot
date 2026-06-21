import telebot
import requests
import json
import os
import base64
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GROQ_KEY = os.environ.get("GROQ_KEY", "")
ADMIN_ID = 5531439198
KARTA_RAQAM = os.environ.get("KARTA_RAQAM", "")
SUMMA = os.environ.get("SUMMA", "10000")
EGASI = os.environ.get("EGASI", "")

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}
user_history = {}

SYSTEM_PROMPT = """Sen professional CV yozishda yordam beruvchi yordamchisan.

Qoidalar:
- Hech qachon o'z ismingni aytma
- Faqat bitta savol ber, bir vaqtda ikkita savol berma
- Qisqa va aniq gapir
- To'g'ri o'zbek tilida yoz: "ayting", "yuboring", "kiriting"
- "biling", "bu eraman" kabi noto'g'ri iboralar ishlatma
- Suhbatni oddiy va tushunarli qil
- Mijoz savol bersa, avval javob ber, keyin o'z savolingni ber

Kerakli ma'lumotlar (birma-bir so'ra):
1. Ism va familiya
2. Yosh
3. Kasb yoki lavozim
4. Ish tajribasi (qayerda, necha yil)
5. Ta'lim (qaysi muassasa, yo'nalish, yili)
6. Bilgan tillari
7. Telefon raqami
8. Email

Barcha ma'lumot to'liq yig'ilgach, MALUMOTLAR_TAYYOR deb yoz va quyidagi formatda yoz:

MALUMOTLAR_TAYYOR
ISM: ...
YOSH: ...
KASB: ...
TAJRIBA: ...
TALIM: ...
TILLAR: ...
TELEFON: ...
EMAIL: ...

Faqat o'zbek tilida (lotin) gapir."""

def ai_javob(chat_id, yangi_xabar):
    if chat_id not in user_history:
        user_history[chat_id] = []

    user_history[chat_id].append({"role": "user", "content": yangi_xabar})

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "max_tokens": 1000,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT}
                ] + user_history[chat_id]
            }
        )
        data = response.json()
        if 'error' in data:
            return f"Xatolik: {data['error']['message']}"
        javob = data["choices"][0]["message"]["content"]
        user_history[chat_id].append({"role": "assistant", "content": javob})
        return javob
    except Exception as e:
        return f"Xatolik: {str(e)}"

def cv_yarat(cv_data):
    prompt = f"""Quyidagi ma'lumotlar asosida professional CV yaz.
Faqat quyidagi formatda yaz, boshqa hech narsa qo'shma:

ISM: {cv_data.get('ISM', '')}
YOSH: {cv_data.get('YOSH', '')}
KASB: {cv_data.get('KASB', '')}
MAQSAD: (2 jumlada professional maqsad yaz)
TAJRIBA: {cv_data.get('TAJRIBA', '')}
TALIM: {cv_data.get('TALIM', '')}
TILLAR: {cv_data.get('TILLAR', '')}
TELEFON: {cv_data.get('TELEFON', '')}
EMAIL: {cv_data.get('EMAIL', '')}
KONIKMA: (kasbga mos 4-5 ta ko'nikma, vergul bilan)"""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    data = response.json()
    return data["choices"][0]["message"]["content"]

def parse_cv(matn):
    natija = {}
    for qator in matn.strip().split('\n'):
        if ':' in qator:
            kalit, qiymat = qator.split(':', 1)
            natija[kalit.strip()] = qiymat.strip()
    return natija

def malumot_ajrat(javob):
    natija = {}
    for qator in javob.split('\n'):
        if ':' in qator:
            kalit, qiymat = qator.split(':', 1)
            kalit = kalit.strip()
            qiymat = qiymat.strip()
            if kalit in ['ISM', 'YOSH', 'KASB', 'TAJRIBA', 'TALIM', 'TILLAR', 'TELEFON', 'EMAIL']:
                natija[kalit] = qiymat
    return natija

def pdf_yarat(cv_data, fayl_nomi):
    doc = SimpleDocTemplate(fayl_nomi, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    sarlavha_stil = ParagraphStyle('Sarlavha', parent=styles['Title'],
        fontSize=22, textColor=colors.HexColor('#1a237e'),
        spaceAfter=5, fontName='Helvetica-Bold')
    kasb_stil = ParagraphStyle('Kasb', parent=styles['Normal'],
        fontSize=12, textColor=colors.HexColor('#3949ab'),
        spaceAfter=3, fontName='Helvetica')
    kontakt_stil = ParagraphStyle('Kontakt', parent=styles['Normal'],
        fontSize=10, textColor=colors.grey,
        spaceAfter=10, fontName='Helvetica')
    bolim_stil = ParagraphStyle('Bolim', parent=styles['Normal'],
        fontSize=13, textColor=colors.HexColor('#1a237e'),
        spaceBefore=12, spaceAfter=4, fontName='Helvetica-Bold')
    matn_stil = ParagraphStyle('Matn', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#333333'),
        spaceAfter=4, fontName='Helvetica', leading=14)

    elementlar = []
    elementlar.append(Paragraph(cv_data.get('ISM', '').upper(), sarlavha_stil))
    elementlar.append(Paragraph(cv_data.get('KASB', ''), kasb_stil))
    elementlar.append(Paragraph(
        f"Tel: {cv_data.get('TELEFON', '')}  |  Email: {cv_data.get('EMAIL', '')}  |  Yosh: {cv_data.get('YOSH', '')}",
        kontakt_stil))
    elementlar.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a237e')))

    for bolim, kalit in [("MAQSAD", "MAQSAD"), ("ISH TAJRIBASI", "TAJRIBA"),
                          ("TA'LIM", "TALIM"), ("TILLAR", "TILLAR"), ("KO'NIKMALAR", "KONIKMA")]:
        elementlar.append(Paragraph(bolim, bolim_stil))
        elementlar.append(Paragraph(cv_data.get(kalit, '-'), matn_stil))
        elementlar.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))

    doc.build(elementlar)

def chek_tekshir(rasm_url):
    image_response = requests.get(rasm_url)
    rasm_base64 = base64.b64encode(image_response.content).decode('utf-8')

    prompt = f"""Bu chek rasmini tahlil qil va faqat JSON formatida javob ber:
{{"karta": "karta raqami", "summa": "summa", "sana": "sana", "togri": true yoki false}}

Tekshirish shartlari:
- Karta raqami {KARTA_RAQAM} ga mos kelishi kerak
- Summa {SUMMA} som bolishi kerak
- Sana bugungi kun bolishi kerak

Faqat JSON yoz."""

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.2-11b-vision-preview",
            "max_tokens": 500,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{rasm_base64}"
                    }},
                    {"type": "text", "text": prompt}
                ]
            }]
        }
    )
    data = response.json()
    matn = data["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
    return json.loads(matn)

def admin_xabar(text, pdf_fayl=None):
    bot.send_message(ADMIN_ID, text)
    if pdf_fayl and os.path.exists(pdf_fayl):
        with open(pdf_fayl, 'rb') as f:
            bot.send_document(ADMIN_ID, f)

def cv_yuborish(cid, message):
    try:
        cv_matn = cv_yarat(user_data[cid]['malumot'])
        cv_data = parse_cv(cv_matn)
        fayl = f"/tmp/cv_{cid}.pdf"
        pdf_yarat(cv_data, fayl)

        matn_cv = (
            "CV TAYYOR!\n\n"
            f"Ism: {cv_data.get('ISM', '')}\n"
            f"Yosh: {cv_data.get('YOSH', '')}\n"
            f"Kasb: {cv_data.get('KASB', '')}\n"
            f"Telefon: {cv_data.get('TELEFON', '')}\n"
            f"Email: {cv_data.get('EMAIL', '')}\n\n"
            f"Maqsad:\n{cv_data.get('MAQSAD', '')}\n\n"
            f"Ish tajribasi:\n{cv_data.get('TAJRIBA', '')}\n\n"
            f"Ta'lim:\n{cv_data.get('TALIM', '')}\n\n"
            f"Tillar:\n{cv_data.get('TILLAR', '')}\n\n"
            f"Ko'nikmalar:\n{cv_data.get('KONIKMA', '')}"
        )

        bot.send_message(cid, matn_cv)
        with open(fayl, 'rb') as f:
            bot.send_document(cid, f, caption="Sizning PDF CV ingiz!")

        username = f"@{message.from_user.username}" if message.from_user.username else "Username yoq"
        admin_xabar(
            f"CV OLDI\n\n"
            f"Ism: {user_data[cid]['malumot'].get('ISM', '')}\n"
            f"Telegram: {username}\n"
            f"ID: {cid}\n"
            f"Telefon: {user_data[cid]['malumot'].get('TELEFON', '')}\n"
            f"Kasb: {user_data[cid]['malumot'].get('KASB', '')}",
            fayl
        )
        os.remove(fayl)

    except Exception as e:
        bot.send_message(cid, f"Xatolik: {str(e)}")

@bot.message_handler(commands=['start'])
def start(message):
    cid = message.chat.id
    user_data[cid] = {'holat': 'suhbat'}
    user_history[cid] = []
    bot.send_message(cid,
        "Salom! CV Bot ga xush kelibsiz!\n\n"
        "Men sizga professional PDF CV yaratib beraman.\n"
        "Narx: 10,000 so'm\n\n"
        "Boshlash uchun /cv yuboring!")

@bot.message_handler(commands=['cv'])
def cv_boshlash(message):
    cid = message.chat.id
    user_data[cid] = {'holat': 'suhbat'}
    user_history[cid] = []
    bot.send_message(cid, "Ismingiz va familiyangizni ayting:")

@bot.message_handler(content_types=['photo'])
def chek_qabul(message):
    cid = message.chat.id
    if cid not in user_data or user_data[cid].get('holat') != 'chek':
        bot.send_message(cid, "Avval /cv buyrug'ini yuboring")
        return

    bot.send_message(cid, "Chek tekshirilmoqda...")

    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        rasm_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        natija = chek_tekshir(rasm_url)

        if natija.get('togri'):
            bot.send_message(cid, "To'lov tasdiqlandi! CV tayyorlanmoqda...")
            cv_yuborish(cid, message)
        else:
            bot.send_message(cid,
                "Chek to'g'ri emas!\n\n"
                "Tekshiring:\n"
                f"Karta: {KARTA_RAQAM}\n"
                f"Summa: {SUMMA} so'm\n"
                "Bugun to'langanmi?\n\n"
                "Qayta yuboring!")

            username = f"@{message.from_user.username}" if message.from_user.username else "Username yoq"
            admin_xabar(
                f"MIJOZ CV OLMADI\n\n"
                f"Ism: {user_data[cid].get('malumot', {}).get('ISM', 'Noaniq')}\n"
                f"Telegram: {username}\n"
                f"ID: {cid}\n"
                f"Sabab: Chek tasdiqlanmadi"
            )

    except Exception as e:
        bot.send_message(cid, f"Chek xatolik: {str(e)}")

@bot.message_handler(func=lambda m: True)
def javob(message):
    cid = message.chat.id

    if cid not in user_data:
        bot.send_message(cid, "Boshlash uchun /start yuboring")
        return

    if user_data[cid].get('holat') == 'chek':
        bot.send_message(cid, "Chek rasmini yuboring")
        return

    if user_data[cid].get('holat') != 'suhbat':
        bot.send_message(cid, "Boshlash uchun /start yuboring")
        return

    bot.send_chat_action(cid, 'typing')
    ai_javob_matn = ai_javob(cid, message.text)

    if 'MALUMOTLAR_TAYYOR' in ai_javob_matn:
        malumot = malumot_ajrat(ai_javob_matn)
        user_data[cid]['malumot'] = malumot
        user_data[cid]['holat'] = 'chek'

        bot.send_message(cid,
            "Barcha ma'lumotlar yig'ildi!\n\n"
            f"To'lov uchun:\n"
            f"Karta: {KARTA_RAQAM}\n"
            f"Miqdor: {SUMMA} so'm\n"
            f"Egasi: {EGASI}\n\n"
            "To'lovdan so'ng chek rasmini yuboring!")

        username = f"@{message.from_user.username}" if message.from_user.username else "Username yoq"
        admin_xabar(
            f"YANGI BUYURTMA\n\n"
            f"Ism: {malumot.get('ISM', '')}\n"
            f"Telegram: {username}\n"
            f"ID: {cid}\n"
            f"Telefon: {malumot.get('TELEFON', '')}\n"
            f"Kasb: {malumot.get('KASB', '')}\n"
            f"Holat: Chek kutilmoqda..."
        )
    else:
        bot.send_message(cid, ai_javob_matn)

print("Bot ishga tushdi!")
bot.polling()
