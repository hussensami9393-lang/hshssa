⭐ Stars → TON Bot

بوت تيليجرام متكامل لتحويل نجوم تيليجرام إلى عملة TON مباشرةً بمحفظة المستخدم.

🚀 المميزات

الميزةالتفاصيل

💱 تحويل فوريالنجوم → TON في 1-3 دقائق

💹 أسعار حيةيتحدث كل 60 ثانية من CoinGecko

💸 عمولة 5%تُخصم تلقائياً قبل الإرسال

🔗 رابط دفعt.me/BOT?start=pay_STARS

👛 محفظة شخصيةيرسل TON مباشرة لمحفظة المستخدم

🌐 موقع ويبمحوّل تفاعلي وجدول أسعار حي

🔧 لوحة إدارةإحصائيات + بث رسائل

📁 هيكل المشروع

stars_ton_bot/
├── bot.py              # نقطة البداية الرئيسية
├── config.py           # الإعدادات
├── database.py         # قاعدة البيانات (SQLite)
├── ton_utils.py        # حساب الأسعار + إرسال TON
├── keyboards.py        # أزرار تيليجرام
├── handlers/
│   ├── start.py        # /start والقائمة الرئيسية
│   ├── wallet.py       # إدارة المحفظة
│   ├── conversion.py   # تدفق التحويل + دفع النجوم
│   └── admin.py        # لوحة الإدارة
├── index.html          # الموقع الرئيسي
├── style.css           # تصميم الموقع
├── animations.css      # انيميشن إضافي
├── app.js              # سكريبت الموقع
├── requirements.txt    # المتطلبات
└── .env.example        # مثال المتغيرات البيئية

⚙️ الإعداد

1. استنساخ المشروع

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

git clone https://github.com/youruser/stars-ton-bot.git

cd stars_ton_bot

2. تثبيت المتطلبات

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

pip install -r requirements.txt

3. إعداد ملف .env

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

cp .env.example .env

nano .env

ثم اعبئ القيم:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

BOT_TOKEN=123456:ABC-DEF...          # توكن البوت من @BotFather

ADMIN_ID=123456789                   # رقم Telegram ID الخاص بك

ADMIN_TON_WALLET=EQxxxx...           # محفظة TON لاستقبال العمولات

TON_API_KEY=                         # اختياري (toncenter.com)

MIN_STARS=50

COMMISSION_PERCENT=5

BOT_USERNAME=YourBotUsername

4. إعداد البوت على @BotFather

/newbot → أنشئ البوت واحصل على التوكن
/setpayments → فعّل مدفوعات الـ Stars

5. تشغيل البوت

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

python bot.py

🌐 الموقع

افتح index.html مباشرةً في المتصفح، أو ارفعه على أي استضافة ثابتة.

قبل الرفع: عدّل BOT_USERNAME في app.js:

[data-radix-scroll-area-viewport]{scrollbar-width:none;-ms-overflow-style:none;-webkit-overflow-scrolling:touch;}[data-radix-scroll-area-viewport]::-webkit-scrollbar{display:none}

const BOT_USERNAME = 'YourActualBotUsername';

🔄 آلية التحويل

المستخدم يدفع X نجمة
         ↓
البوت يستلم النجوم عبر Telegram Stars API
         ↓
يحسب القيمة: X × $0.013 = $VALUE
         ↓
يقسم على سعر TON الحالي: $VALUE ÷ $TON_PRICE = TON_TOTAL
         ↓
يخصم 5% عمولة → يرسلها لمحفظة الأدمن
         ↓
يرسل 95% TON → محفظة المستخدم
         ↓
يسجل المعاملة في قاعدة البيانات

📊 أوامر الأدمن

الأمرالوظيفة

/adminلوحة الإدارة الرئيسية

/broadcast <msg>بث رسالة لجميع المستخدمين

⚠️ ملاحظات مهمة

- إرسال TON: يتطلب محفظة custodial ممولة على السيرفر. في الإنتاج استخدم @wallet bot أو TON Connect لإدارة المحفظة.

- الأمان: لا تشارك ملف .env أبداً.

- النسخ الاحتياطي: احتفظ بنسخة من bot_database.db بانتظام.

📜 الترخيص

MIT License — للاستخدام الشخصي والتجاري.