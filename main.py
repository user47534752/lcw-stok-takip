import os
import requests
import json
from bs4 import BeautifulSoup

# ---- AYARLAR ----
URUN_URL = "https://www.lcw.com/bisiklet-yaka-uzun-kollu-erkek-kalin-sweatshirt-siyah-o-3370422"
TAKIP_EDILEN_BEDEN = "XS"
STATE_FILE = "state.json" # Stok bildiriminin daha önce yapılıp yapılmadığını takip etmek için

# GitHub Secrets'tan Telegram bilgilerini çek
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')
# ---- AYARLAR SONU ----

def telegram_bildirim_gonder(mesaj):
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

def stok_kontrol_et():
    print(f"Sayfa taranıyor: {URUN_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        r = requests.get(URUN_URL, headers=headers, timeout=15)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        size_buttons = soup.select('div.product-size-selector__buttons-container a.product-size-selector__button')
        
        hedef_buton = None
        for button in size_buttons:
            if button.text.strip() == TAKIP_EDILEN_BEDEN:
                hedef_buton = button
                break
                
        if not hedef_buton:
            print(f"{TAKIP_EDILEN_BEDEN} bedeni sayfada bulunamadı.")
            return

        if 'disabled' in hedef_buton.get('class', []):
            print(f">>> Durum stabil. {TAKIP_EDILEN_BEDEN} bedeni stokta yok.")
        else:
            print(f">>> MÜJDE! {TAKIP_EDILEN_BEDEN} bedeni STOKTA GÖRÜNÜYOR!")
            telegram_bildirim_gonder(f"✅ Ürün STOĞA GİRDİ!\n\n{URUN_URL}")
            # Stoğa girdiği için script'in bir sonraki sefer çalışmaması için hata koduyla çıkış yapabiliriz.
            # Bu, GitHub Actions'ın görevi 'başarısız' görmesini sağlar ve tekrar çalışmasını (bazı ayarlarda) engeller.
            # Şimdilik sadece bildirimi gönderip normal bitiriyoruz.
            
    except Exception as e:
        print(f"!!! Bir Hata Oluştu: {e}")

if __name__ == "__main__":
    stok_kontrol_et()