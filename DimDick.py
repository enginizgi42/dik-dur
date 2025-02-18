import cv2
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import queue

# Yüz tespiti için önceden eğitilmiş modeli yükle
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Kamera başlat
cap = cv2.VideoCapture(0)

# Tkinter penceresi oluştur
root = tk.Tk()
root.withdraw()  # Ana pencereyi başlangıçta gizle

# Uyarı penceresinin durumunu takip etmek için bir değişken
warning_shown = False

# Thread'ler arası iletişim için bir kuyruk
message_queue = queue.Queue()

# Yüzün boyutu için eşik değerleri
FACE_SIZE_THRESHOLD_HIGH = 35000  # 50000 ayarını verebilirsin. bu ayarla oyna. Uyarı penceresini açmak için eşik değer
FACE_SIZE_THRESHOLD_LOW = 30000   # Uyarı penceresini kapatmak için eşik değer

def show_warning():
    global warning_shown
    if not warning_shown:
        # Tam ekran uyarı penceresi oluştur
        root.deiconify()  # Pencereyi göster
        root.attributes('-fullscreen', True)# Tam ekran yap
        root.attributes('-topmost', True)
        root.configure(bg='green')  # Arka plan rengi
        label = tk.Label(root, text="DİK DUR!", font=("Arial", 100), fg="white", bg="green")
        label.pack(expand=True)
        warning_shown = True

def hide_warning():
    global warning_shown
    if warning_shown:
        # Uyarı penceresini gizle
        root.withdraw()
        warning_shown = False

def check_posture(face_size):
    # Yüzün boyutunu kontrol et
    if face_size > FACE_SIZE_THRESHOLD_HIGH:
        message_queue.put("show")
    elif face_size < FACE_SIZE_THRESHOLD_LOW:
        message_queue.put("hide")

def camera_thread():
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Gri tonlamaya çevir
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Yüzleri tespit et
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Yüz tespit edildiyse
        if len(faces) > 0:
            for (x, y, w, h) in faces:
                # Yüzün etrafına dikdörtgen çiz (bu çizim ekranda görünmeyecek, sadece işlem yapılacak)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                # Yüzün boyutunu hesapla (genişlik * yükseklik)
                face_size = w * h

                # Duruşu kontrol et
                check_posture(face_size)
        else:
            # Yüz tespit edilmediyse uyarıyı gizle
            message_queue.put("hide")

        # Görüntüyü gösterme kısmını kaldırıyoruz, böylece kamera ekranı görünmeyecek.

        # Çıkış için 'q' tuşuna bas
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Temizlik
    cap.release()
    cv2.destroyAllWindows()
    message_queue.put("exit")  # Programı sonlandır

# Tkinter penceresini güncelle
def update_gui():
    try:
        while True:
            message = message_queue.get_nowait()
            if message == "show":
                show_warning()
            elif message == "hide":
                hide_warning()
            elif message == "exit":
                root.quit()
                break
    except queue.Empty:
        pass
    root.after(100, update_gui)  # Her 100 ms'de bir GUI'yi güncelle

# Kamera thread'ini başlat
camera_thread = Thread(target=camera_thread)
camera_thread.daemon = True
camera_thread.start()

# Tkinter ana döngüsünü başlat
root.after(100, update_gui)
root.mainloop()
