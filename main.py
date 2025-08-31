import os
import requests
from bs4 import BeautifulSoup

# ---- AYARLAR ----
URUN_URL = "https://www.lcw.com/bisiklet-yaka-uzun-kollu-erkek-kalin-sweatshirt-siyah-o-3370422"
TAKIP_EDILEN_BEDEN = "XS"

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

def stok_kontrol_et():
    """Ana stok kontrol fonksiyonu."""
    print(f"Sayfa taranıyor: {URUN_URL}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
    }
    
    try:
        r = requests.get(URUN_URL, headers=headers, timeout=15)
        r.raise_for_status()  # HTTP hatası varsa programı durdur
        
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Sizin bulduğunuz yeni yapıya göre tüm beden butonlarını buluyoruz.
        # Artık 'button' etiketlerini ve 'option-size-box' class'ını arıyoruz.
        size_buttons = soup.select('button.option-size-box')
        
        hedef_buton = None
        for button in size_buttons:
            # Butonun içindeki metni alıp boşluklardan arındırıyoruz.
            if button.text.strip() == TAKIP_EDILEN_BEDEN:
                hedef_buton = button
                break
                
        if not hedef_buton:
            print(f"'{TAKIP_EDILEN_BEDEN}' bedeni sayfada bulunamadı. Sayfa yapısı değişmiş olabilir.")
            return

        # Butonun class listesini alıyoruz.
        button_classes = hedef_buton.get('class', [])
        
        # Eğer class listesi içinde 'option-size-box__out-of-stock' varsa, ürün stokta yoktur.
        if 'option-size-box__out-of-stock' in button_classes:
            print(f">>> Durum stabil. '{TAKIP_EDILEN_BEDEN}' bedeni stokta yok.")
        else:
            # Eğer bu class yoksa, ürün stoğa girmiş demektir!
            print(f">>> MÜJDE! '{TAKIP_EDILEN_BEDEN}' bedeni STOKTA GÖRÜNÜYOR!")
            telegram_bildirim_gonder(f"✅ Ürün STOĞA GİRDİ!\n\n{URUN_URL}")
            
    except requests.exceptions.RequestException as e:
        print(f"!!! Siteye bağlanırken bir hata oluştu: {e}")
    except Exception as e:
        print(f"!!! Beklenmedik bir hata oluştu: {e}")

if __name__ == "__main__":
    stok_kontrol_et()
