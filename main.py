import os
import time
import requests
import json
from bs4 import BeautifulSoup

# ---- AYARLAR ----
URUN_URL = "https://www.lcw.com/bisiklet-yaka-uzun-kollu-erkek-kalin-sweatshirt-siyah-o-3370422"
TAKIP_EDILEN_BEDEN = "XS"
# Sayaç ve zaman bilgilerini proje klasöründe bu dosyada tutacak
STATE_FILE = "state.json" 

# GitHub Secrets'tan Telegram bilgilerini çek
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
# ---- AYARLAR SONU ----


def telegram_bildirim_gonder(mesaj):
    """Belirtilen mesajı Telegram'a gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bilgileri (Secrets) ayarlanmamış.")
        return
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': mesaj, 'parse_mode': 'HTML'}
    try:
        requests.post(api_url, data=payload, timeout=10)
        print("Telegram bildirimi gönderildi.")
    except Exception as e:
        print(f"Telegram hatası: {e}")

def load_state():
    """Hafıza dosyasından (state.json) sayaçları ve zamanı yükler."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Eğer dosya yoksa, varsayılan değerlerle başlat
        return {'successful_scans': 0, 'failed_scans': 0, 'last_report_timestamp': 0, 'notified_in_stock': False}

def save_state(state):
    """Sayaçları ve zamanı hafıza dosyasına kaydeder."""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def gunluk_rapor_gonder(state):
    """Günlük özet raporunu Telegram'a gönderir."""
    print("Günlük rapor gönderme zamanı geldi...")
    rapor_mesaji = (f"📊 LCW Stok Takip Günlük Raporu 📊\n\n"
                    f"Son 24 saatlik çalışma özeti:\n"
                    f"✅ Başarılı Tarama: {state['successful_scans']}\n"
                    f"❌ Hatalı Tarama: {state['failed_scans']}")
    telegram_bildirim_gonder(rapor_mesaji)

def stok_kontrol_et():
    """Ana stok kontrol fonksiyonu."""
    print(f"Sayfa taranıyor: {URUN_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    r = requests.get(URUN_URL, headers=headers, timeout=15)
    r.raise_for_status()
    
    soup = BeautifulSoup(r.text, "html.parser")
    size_buttons = soup.select('button.option-size-box')
    
    hedef_buton = None
    for button in size_buttons:
        if button.text.strip() == TAKIP_EDILEN_BEDEN:
            hedef_buton = button
            break
            
    if not hedef_buton:
        raise Exception(f"'{TAKIP_EDILEN_BEDEN}' bedeni sayfada bulunamadı.")

    button_classes = hedef_buton.get('class', [])
    
    if 'option-size-box__out-of-stock' in button_classes:
        print(f">>> Durum stabil. '{TAKIP_EDILEN_BEDEN}' bedeni stokta yok.")
        return False
    else:
        print(f">>> MÜJDE! '{TAKIP_EDILEN_BEDEN}' bedeni STOKTA GÖRÜNÜYOR!")
        return True

# --- ANA ÇALIŞTIRMA MANTIĞI (RAPORLAMA İLE BİRLİKTE) ---
if __name__ == "__main__":
    state = load_state()
    
    try:
        stokta_mi = stok_kontrol_et()
        state['successful_scans'] += 1
        
        if stokta_mi:
            if not state.get('notified_in_stock', False):
                print("Ürün stoğa yeni girdi! Bildirim gönderiliyor.")
                telegram_bildirim_gonder(f"✅ Ürün STOĞA GİRDİ!\n\n{URUN_URL}")
                state['notified_in_stock'] = True
        else:
            state['notified_in_stock'] = False
    
    except Exception as e:
        print(f"!!! Bir Hata Oluştu: {e}")
        state['failed_scans'] += 1
    
    # Raporlama zamanını kontrol et
    current_time = time.time()
    if current_time - state.get('last_report_timestamp', 0) > 86400: # 86400 saniye = 24 saat
        gunluk_rapor_gonder(state)
        state['successful_scans'] = 0
        state['failed_scans'] = 0
        state['last_report_timestamp'] = current_time
    
    save_state(state)
    print("Kontrol tamamlandı.")
