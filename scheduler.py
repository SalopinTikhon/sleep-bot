import time, threading
from config import now_msk
from database import cur, conn, update_field

def check_sleep_loop(bot):
    while True:
        now = now_msk()
        cur_hhmm = now.strftime("%H:%M")
        ts = time.time()
        cur.execute("SELECT user_id, coins, bedtime, status, ping_ts, warned, rival_id, bet FROM users")
        for uid, coins, bedtime, status, ping_ts, warned, rival_id, bet in cur.fetchall():
            if cur_hhmm == bedtime and status == "awake":
                update_field(uid, "status", "pinged")
                update_field(uid, "ping_ts", ts)
                update_field(uid, "warned", 0)
                try: bot.send_message(uid, "⏰ Время отбоя! Нажми «😴 Я лёг спать» внизу, иначе через 7 минут штраф!")
                except Exception: pass
            elif status == "pinged" and ping_ts > 0:
                diff = (ts - ping_ts) / 60.0
                if diff >= 7 and warned == 0:
                    update_field(uid, "coins", max(0, coins - 10))
                    update_field(uid, "warned", 1)
                    try: bot.send_message(uid, "⚠️ Прошло 7 минут! Снято 10 штрафных монет. Ещё 13 минут — и батл проигран!")
                    except Exception: pass
                elif diff >= 20:
                    update_field(uid, "status", "awake")
                    update_field(uid, "ping_ts", 0)
                    msg = "❌ Прошло 20 минут! Ты проспал отбой."
                    if rival_id:
                        cur.execute("UPDATE users SET coins=coins+?, rival_id=0, bet=0 WHERE user_id=?", (bet * 2, rival_id))
                        update_field(uid, "rival_id", 0)
                        update_field(uid, "bet", 0)
                        conn.commit()
                        msg += f" Батл проигран, {bet} монет ушли сопернику!"
                        try: bot.send_message(rival_id, f"🏆 Соперник проспал отбой! Ты выиграл {bet * 2} монет!")
                        except Exception: pass
                    try: bot.send_message(uid, msg)
                    except Exception: pass
        time.sleep(30)

def start_scheduler(bot):
    threading.Thread(target=check_sleep_loop, args=(bot,), daemon=True).start()
