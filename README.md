### FILE: README.md
# SozMaster AI

SozMaster AI — bu aiogram 3 asosidagi Telegram bot bo'lib, foydalanuvchilarga inglizcha so'zlarni o'zbek tilida qulay tarzda o'rganishga yordam beradi. Bot har kuni yangi so'zlarni yuboradi, mini-quizlar orqali bilimni mustahkamlaydi va XP tizimi bilan rag'batlantiradi. Premium foydalanuvchilar uchun qo'shimcha imkoniyatlar mavjud.

## Asosiy imkoniyatlar
- Har kuni 5 ta (Premium foydalanuvchilar uchun 20 ta) yangi so'z
- Qiziqarli fill-in-the-blank mashqlari
- Interaktiv quizlar va XP tizimi
- O'zbek tilidagi qulay interfeys
- Premium rejim uchun tayyor infratuzilma (manual /make_premium buyruqlari)

## Talablar
- Python 3.11+
- Telegram bot tokeni

## O'rnatish va ishga tushirish (lokal)
1. Reponi yuklab oling yoki klon qiling.
2. Virtual muhit yarating va faollashtiring:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Kerakli kutubxonalarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
4. Loyihaning ildizida `.env` faylini yarating:
   ```env
   TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   ADMIN_USER_IDS=123456789,987654321
   ```
   `ADMIN_USER_IDS` — bu `/make_premium` buyruqlarini ishlata oladigan administratorlar ro'yxati (vergul bilan ajratilgan Telegram ID'lar).
5. Botni ishga tushiring:
   ```bash
   python bot.py
   ```

## Ishga tushirish (VPS / production)
1. VPS'da Python 3.11 o'rnatilganligiga ishonch hosil qiling.
2. Reponi serverga yuboring (git pull/scp).
3. Loyiha papkasida virtual muhit yarating va faollashtiring:
   ```bash
   python3 -m venv /opt/sozmaster-ai/.venv
   source /opt/sozmaster-ai/.venv/bin/activate
   ```
4. Talablarni o'rnating:
   ```bash
   pip install -r requirements.txt
   ```
5. `.env` faylini serverda yarating (token va admin ID'lar bilan).
6. Botni fon rejimida ishga tushirish uchun `screen` yoki `tmux`dan foydalaning:
   ```bash
   screen -S sozmaster
   python bot.py
   # Sessiyani tark etish: Ctrl+A, keyin D
   ```
7. Yoki `systemd` xizmatini sozlash uchun quyidagi oddiy unit faylidan foydalaning:
   ```ini
   [Unit]
   Description=SozMaster AI Telegram bot
   After=network.target

   [Service]
   Type=simple
   WorkingDirectory=/opt/sozmaster-ai
   Environment="TELEGRAM_BOT_TOKEN=YOUR_TOKEN"
   Environment="ADMIN_USER_IDS=123456789"
   ExecStart=/opt/sozmaster-ai/.venv/bin/python /opt/sozmaster-ai/bot.py
   Restart=always
   User=botuser

   [Install]
   WantedBy=multi-user.target
   ```
   Unit faylini `/etc/systemd/system/sozmaster.service` sifatida saqlang, so'ngra:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable sozmaster
   sudo systemctl start sozmaster
   sudo systemctl status sozmaster
   ```

## Ma'lumotlar bazasi
Bot `bot.db` nomli SQLite faylidan foydalanadi. Fayl avtomatik yaratiladi va migratsiyalar talab etilmaydi.

## Loyihani test qilish
- `/start` — botni boshlash
- `/today` — bugungi so'zlarni olish
- `/quiz` — quizni ishga tushirish
- `/stats` — XP va streak ma'lumotlari
- `/upgrade` — Premium rejim haqida ma'lumot
- `/make_premium <user_id> [kunlar]` — adminlar uchun Premium berish

Bot barcha xabarlarni o'zbek tilida yuboradi va Premium funksiyalar uchun tayyor tuzilmani taqdim etadi.

