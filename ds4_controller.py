"""
DualShock 4 Kontrol Paneli
Geliştirici: rtx4090
"""

import sys
import pygame
import hid
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QSlider, QLabel, QPushButton, QMessageBox,
                           QColorDialog, QSplashScreen)
from PyQt5.QtCore import Qt, QTimer, QThread, QSize
from PyQt5.QtGui import QMovie, QPixmap, QPainter, QColor, QFont, QPen, QLinearGradient
import time

class LoadingScreen(QSplashScreen):
    def __init__(self):
        super().__init__()
        # Ekran boyutlarını al
        screen = QApplication.primaryScreen().geometry()
        
        # Loader boyutları
        width = 500
        height = 400
        
        # Loader'ı ekranın ortasına konumlandır
        x = (screen.width() - width) // 2
        y = (screen.height() - height) // 2
        
        # Pencere bayraklarını güncelle - tıklamayı engelle
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WA_TranslucentBackground | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFixedSize(width, height)
        self.move(x, y)
        
        # Arka plan rengi ve stil
        self.background_color = QColor(28, 35, 45)  # Koyu arka plan
        self.text_color = QColor(52, 152, 219)  # Neon mavi
        self.accent_color = QColor(46, 204, 113)  # Yeşil
        self.loading_dots = 0
        self.loading_text = "DualShock 4 Kontrol Paneli Yükleniyor"
        self.angle = 0  # Dönen animasyon için açı
        
        # Yükleme animasyonu için timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_loading)
        self.timer.start(50)  # Her 50ms'de bir güncelle
        
        # Yükleme yüzdesi
        self.progress = 0
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(30)
    
    def update_loading(self):
        self.loading_dots = (self.loading_dots + 1) % 4
        self.angle = (self.angle + 10) % 360  # Dönen animasyon için açıyı güncelle
        self.repaint()
    
    def update_progress(self):
        if self.progress < 100:
            self.progress += 1
            self.repaint()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Arka plan
        painter.fillRect(self.rect(), self.background_color)
        
        # Dönen daire animasyonu
        center = self.rect().center()
        painter.translate(center)
        painter.rotate(self.angle)
        
        for i in range(8):
            painter.save()
            painter.rotate(i * 45)
            color = self.accent_color
            color.setAlpha(255 - ((i * 255) // 8))
            painter.setPen(QPen(color, 4))
            painter.drawLine(50, 0, 70, 0)
            painter.restore()
        
        painter.resetTransform()
        
        # Başlık
        painter.setFont(QFont('Arial', 24, QFont.Bold))
        painter.setPen(self.text_color)
        title = "DualShock 4 Kontrol Paneli"
        title_rect = painter.boundingRect(self.rect(), Qt.AlignHCenter | Qt.AlignTop, title)
        painter.drawText(title_rect.adjusted(0, 50, 0, 0), Qt.AlignHCenter, title)
        
        # Geliştirici bilgisi
        painter.setFont(QFont('Arial', 14))
        dev_text = "Geliştirici: rtx4090"
        dev_rect = painter.boundingRect(self.rect(), Qt.AlignHCenter | Qt.AlignTop, dev_text)
        painter.drawText(dev_rect.adjusted(0, 100, 0, 0), Qt.AlignHCenter, dev_text)
        
        # Yükleme metni ve animasyonu
        dots = "." * self.loading_dots
        loading_text = self.loading_text + dots
        painter.setFont(QFont('Arial', 14))
        text_rect = painter.boundingRect(self.rect(), Qt.AlignHCenter | Qt.AlignBottom, loading_text)
        painter.drawText(text_rect.adjusted(0, 0, 0, -100), Qt.AlignHCenter, loading_text)
        
        # İlerleme çubuğu arka planı
        bar_width = 300
        bar_height = 6
        x = (self.width() - bar_width) // 2
        y = self.height() - 80
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(44, 62, 80))
        painter.drawRoundedRect(x, y, bar_width, bar_height, 3, 3)
        
        # İlerleme çubuğu
        progress_width = int(bar_width * (self.progress / 100))
        gradient = QLinearGradient(x, y, x + bar_width, y)
        gradient.setColorAt(0, self.text_color)
        gradient.setColorAt(1, self.accent_color)
        painter.setBrush(gradient)
        painter.drawRoundedRect(x, y, progress_width, bar_height, 3, 3)
        
        # Yüzde metni
        percent_text = f"%{self.progress}"
        painter.setPen(self.text_color)
        percent_rect = painter.boundingRect(self.rect(), Qt.AlignHCenter | Qt.AlignBottom, percent_text)
        painter.drawText(percent_rect.adjusted(0, 0, 0, -50), Qt.AlignHCenter, percent_text)

    def mousePressEvent(self, event):
        # Tıklama olaylarını engelle
        pass

class DS4Controller:
    def __init__(self):
        self.device = None
        # DualShock 4 için olası Vendor ID ve Product ID'ler
        self.vendor_id = 0x054C  # Sony
        self.product_ids = [
            0x09CC,  # DualShock 4 v2
            0x05C4,  # DualShock 4 v1
            0x0BA0,  # DualShock 4 USB Wireless Adaptor
        ]
        
    def connect(self):
        try:
            # Tüm HID cihazlarını bul
            print("Bulunan tüm HID cihazları:")
            for device in hid.enumerate():
                print(f"VID: {device['vendor_id']:04x}, PID: {device['product_id']:04x}, Path: {device['path']}")
            
            # DualShock 4'ü bul
            ds4_devices = [dev for dev in hid.enumerate() 
                          if dev['vendor_id'] == self.vendor_id and dev['product_id'] in self.product_ids]
            
            if ds4_devices:
                self.device = hid.device()
                self.device.open_path(ds4_devices[0]['path'])
                self.device.set_nonblocking(True)
                print(f"Bağlanılan kontrolcü: VID={ds4_devices[0]['vendor_id']:04x}, PID={ds4_devices[0]['product_id']:04x}")
                
                # Pil durumunu kontrol et
                print("Pil durumu kontrol ediliyor...")
                self.get_battery_level()
                
                return True
            else:
                print("DualShock 4 bulunamadı")
                return False
                
        except Exception as e:
            print(f"Bağlantı hatası: {e}")
            return False
    
    def disconnect(self):
        if self.device:
            self.device.close()
            self.device = None
    
    def set_vibration(self, small_motor, big_motor):
        # Titreşim değerlerini 0-255 arasına sınırla
        small_motor = max(0, min(255, int(small_motor)))
        big_motor = max(0, min(255, int(big_motor)))
        
        # USB HID rapor formatı - Report ID: 0x05
        report = [
            0x05,  # Report ID
            0x01,  # Motor enable
            0x00,  # Reserved
            0x00,  # Reserved
            0x00,  # Reserved
            big_motor,   # Büyük motor (sol)
            small_motor, # Küçük motor (sağ)
            0x00,  # LED Kırmızı
            0x00,  # LED Yeşil
            0x00,  # LED Mavi
            0x00,  # LED Parlak
            0x00,  # LED Flash On
            0x00,  # LED Flash Off
            0x00   # Reserved
        ]
        
        print(f"Titreşim raporu gönderiliyor: {report}")
        print(f"Titreşim değerleri - Sol: {big_motor}, Sağ: {small_motor}")
        
        try:
            self.device.write(report)
        except Exception as e:
            print(f"Titreşim raporu gönderilirken hata oluştu: {e}")

    def set_led_color(self, red, green, blue):
        # LED değerlerini 0-255 arasına sınırla
        red = max(0, min(255, int(red)))
        green = max(0, min(255, int(green)))
        blue = max(0, min(255, int(blue)))
        
        # USB HID rapor formatı - Report ID: 0x05
        report = [
            0x05,  # Report ID
            0x01,  # Motor enable
            0x00,  # Reserved
            0x00,  # Reserved
            0x00,  # Reserved
            0x00,  # Küçük motor
            0x00,  # Büyük motor
            red,   # LED Kırmızı
            green, # LED Yeşil
            blue,  # LED Mavi
            0xFF,  # LED Parlak
            0x00,  # LED Flash On
            0x00,  # LED Flash Off
            0x00   # Reserved
        ]
        
        print(f"LED raporu gönderiliyor: {report}")
        print(f"LED değerleri - R: {red}, G: {green}, B: {blue}")
        
        try:
            self.device.write(report)
            time.sleep(0.05)  # Renk değişimi için kısa bekleme
        except Exception as e:
            print(f"LED raporu gönderilirken hata oluştu: {e}")

    def get_battery_level(self):
        try:
            if self.device:
                # Birkaç deneme yap
                for _ in range(5):
                    try:
                        # Durum raporunu oku
                        data = self.device.read(64)
                        if data and len(data) >= 32:  # Doğru rapor uzunluğu
                            battery_level = (data[30] & 0x0f) * 10  # 0-100 arası değer
                            is_charging = (data[30] & 0x10) != 0
                            
                            print(f"Ham veri: {data}")
                            print(f"Pil Seviyesi: %{battery_level}")
                            print(f"Şarj Oluyor: {'Evet' if is_charging else 'Hayır'}")
                            return battery_level, is_charging
                    except Exception as e:
                        print(f"Okuma denemesi hatası: {e}")
                    time.sleep(0.1)
                
                print("Pil seviyesi okunamadı")
                return None, None
                
        except Exception as e:
            print(f"Pil seviyesi okuma hatası: {e}")
        return None, None

    def vibration_pattern(self, pattern_name):
        if pattern_name == "artan":
            # Gittikçe artan titreşim
            for i in range(0, 255, 5):
                self.set_vibration(i, i)
                time.sleep(0.05)
        elif pattern_name == "dalgali":
            # Dalgalı titreşim
            for _ in range(2):
                for i in range(0, 255, 10):
                    self.set_vibration(i, 255-i)
                    time.sleep(0.05)
                for i in range(255, 0, -10):
                    self.set_vibration(i, 255-i)
                    time.sleep(0.05)
        elif pattern_name == "nabiz":
            # Nabız gibi titreşim
            for _ in range(3):
                self.set_vibration(255, 255)
                time.sleep(0.2)
                self.set_vibration(0, 0)
                time.sleep(0.2)
        elif pattern_name == "soft":
            # Yumuşak titreşim
            for _ in range(2):
                for i in range(0, 128, 5):
                    self.set_vibration(i, i)
                    time.sleep(0.1)
                for i in range(128, 0, -5):
                    self.set_vibration(i, i)
                    time.sleep(0.1)
        # Son olarak titreşimi durdur
        self.set_vibration(0, 0)

class DS4ControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('DualShock 4 Kontrol Paneli - by rtx4090')
        self.setGeometry(100, 100, 1200, 600)  # Genişliği artırdık
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
            }
            QLabel {
                color: #ecf0f1;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2574a9;
            }
            QSlider {
                height: 25px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #3498db;
                height: 10px;
                background: #34495e;
                margin: 0px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: none;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: #2980b9;
            }
        """)
        
        # Pygame başlatma
        pygame.init()
        pygame.joystick.init()
        
        # DS4 kontrolcüsü oluştur
        self.ds4 = DS4Controller()
        
        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)  # Ana layout'u yatay yaptık
        
        # Sol taraf için layout
        left_layout = QVBoxLayout()
        
        # Bağlantı bilgileri
        self.info_label = QLabel('''Bluetooth Bağlantı Adımları:
1. PS + SHARE butonlarına aynı anda basılı tutun
2. Işık çubuğu hızlı yanıp sönene kadar bekleyin
3. Windows Bluetooth ayarlarından "Wireless Controller"ı eşleştirin
4. Aşağıdaki "Kontrolcüye Bağlan" butonuna tıklayın

Geliştirici: rtx4090''')
        self.info_label.setStyleSheet("""
            QLabel { 
                background-color: #34495e; 
                color: #ecf0f1;
                padding: 15px; 
                border-radius: 8px;
                font-size: 13px;
            }
        """)
        left_layout.addWidget(self.info_label)
        
        # Titreşim kontrolü için slider'lar
        self.create_vibration_controls(left_layout)
        
        # LED kontrolü için renk seçici
        self.create_led_controls(left_layout)
        
        # Yenile ve bağlantı butonları
        self.refresh_button = QPushButton('Kontrolcüleri Yenile')
        self.refresh_button.clicked.connect(self.refresh_controllers)
        left_layout.addWidget(self.refresh_button)
        
        self.connect_button = QPushButton('Kontrolcüye Bağlan')
        self.connect_button.clicked.connect(self.connect_controller)
        self.connect_button.setStyleSheet("QPushButton { padding: 10px; }")
        left_layout.addWidget(self.connect_button)
        
        # Durum etiketi
        self.status_label = QLabel('Durum: Bağlı değil | Geliştirici: rtx4090')
        self.status_label.setStyleSheet("QLabel { color: red; }")
        left_layout.addWidget(self.status_label)
        
        # Sol layoutu ana layouta ekle
        main_layout.addLayout(left_layout)
        
        # Sağ taraf için layout (Tuş testi)
        right_layout = QVBoxLayout()
        self.create_button_test_section(right_layout)
        main_layout.addLayout(right_layout)
        
        # Kontrolcü değişkenleri
        self.controller = None
        self.is_connected = False
        
        # Timer for controller status check
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_controller)
        self.timer.start(3000)
        
        # Timer for button states update
        self.button_timer = QTimer()
        self.button_timer.timeout.connect(self.update_button_states)
        self.button_timer.start(50)  # 50ms aralıklarla güncelle (20 FPS)
    
    def refresh_controllers(self):
        try:
            debug_info = "Bulunan HID cihazları:\n"
            for device in hid.enumerate():
                if device['vendor_id'] == 0x054C:  # Sony
                    debug_info += f"VID: {device['vendor_id']:04x}, PID: {device['product_id']:04x}, Path: {device['path']}\n"
            
            self.debug_label.setText(debug_info)
            QMessageBox.information(self, 'Yenileme', f'Cihazlar yenilendi.\n\n{debug_info}')
        except Exception as e:
            print(f"Yenileme hatası: {e}")
    
    def create_button_test_section(self, layout):
        # Grup başlığı
        button_test_label = QLabel('Tuş Testi')
        button_test_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 16px;
                color: #3498db;
                margin-top: 15px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(button_test_label)
        
        # Tuş durumlarını gösterecek etiketler için grid
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)  # Tuşlar arası boşluğu artırdık
        
        # Tuş etiketleri için ortak stil - Büyütülmüş ve daha belirgin
        button_style = """
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 12px;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                min-width: 80px;
                font-size: 16px;
                font-weight: bold;
            }
        """
        
        # Sol taraf tuşları
        left_buttons = QVBoxLayout()
        left_buttons.setSpacing(8)  # Dikey boşluk
        self.button_labels = {}
        
        # D-Pad tuşları
        dpad_buttons = ['↑', '↓', '←', '→']
        for btn in dpad_buttons:
            self.button_labels[btn] = QLabel(f'{btn}: ⬛')
            self.button_labels[btn].setStyleSheet(button_style)
            left_buttons.addWidget(self.button_labels[btn])
        
        # Ana tuşlar
        main_buttons = ['□', '○', '×', '△']
        for btn in main_buttons:
            self.button_labels[btn] = QLabel(f'{btn}: ⬛')
            self.button_labels[btn].setStyleSheet(button_style)
            left_buttons.addWidget(self.button_labels[btn])
        
        button_layout.addLayout(left_buttons)
        
        # Orta tuşlar
        middle_buttons = QVBoxLayout()
        special_buttons = ['SHARE', 'OPTIONS', 'PS', 'TOUCHPAD']
        for btn in special_buttons:
            self.button_labels[btn] = QLabel(f'{btn}: ⬛')
            self.button_labels[btn].setStyleSheet(button_style)
            middle_buttons.addWidget(self.button_labels[btn])
        
        button_layout.addLayout(middle_buttons)
        
        # Sağ taraf (Tetik ve Bumper tuşları)
        right_buttons = QVBoxLayout()
        trigger_buttons = ['L1', 'L2', 'R1', 'R2', 'L3', 'R3']
        for btn in trigger_buttons:
            self.button_labels[btn] = QLabel(f'{btn}: ⬛')
            self.button_labels[btn].setStyleSheet(button_style)
            right_buttons.addWidget(self.button_labels[btn])
        
        button_layout.addLayout(right_buttons)
        layout.addLayout(button_layout)
        
        # Analog çubuk değerleri için etiketler
        sticks_layout = QHBoxLayout()
        
        # Sol analog
        left_stick = QVBoxLayout()
        self.left_stick_label = QLabel('Sol Analog: X: 0, Y: 0')
        self.left_stick_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid gray;
                border-radius: 3px;
            }
        """)
        left_stick.addWidget(self.left_stick_label)
        sticks_layout.addLayout(left_stick)
        
        # Sağ analog
        right_stick = QVBoxLayout()
        self.right_stick_label = QLabel('Sağ Analog: X: 0, Y: 0')
        self.right_stick_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 5px;
                border: 1px solid gray;
                border-radius: 3px;
            }
        """)
        right_stick.addWidget(self.right_stick_label)
        sticks_layout.addLayout(right_stick)
        
        layout.addLayout(sticks_layout)
    
    def create_vibration_controls(self, layout):
        # Grup başlığı
        controls_label = QLabel('Titreşim Kontrolleri')
        controls_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #3498db;
                margin-top: 15px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(controls_label)
        
        # Titreşim modları için butonlar
        patterns_layout = QHBoxLayout()
        patterns_layout.setSpacing(10)  # Butonlar arası boşluk
        patterns = {
            'Artan': 'artan',
            'Dalgalı': 'dalgali',
            'Nabız': 'nabiz',
            'Yumuşak': 'soft'
        }
        
        for pattern_name, pattern_id in patterns.items():
            btn = QPushButton(pattern_name)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2ecc71;
                    color: white;
                    min-width: 90px;
                    padding: 10px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #27ae60;
                }
                QPushButton:pressed {
                    background-color: #219a52;
                }
            """)
            btn.clicked.connect(lambda checked, p=pattern_id: self.vibration_pattern(p))
            patterns_layout.addWidget(btn)
        
        # Titreşimi durdur butonu
        stop_btn = QPushButton('Titreşimi Durdur')
        stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                min-width: 90px;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        stop_btn.clicked.connect(lambda: self.ds4.set_vibration(0, 0) if self.is_connected else None)
        patterns_layout.addWidget(stop_btn)
        
        layout.addLayout(patterns_layout)
        
        # Manuel titreşim kontrolü
        manual_label = QLabel('Manuel Titreşim:')
        layout.addWidget(manual_label)
        
        # Sol motor kontrolü
        left_layout = QHBoxLayout()
        left_label = QLabel('Sol Motor:')
        self.left_slider = QSlider(Qt.Horizontal)
        self.left_slider.setRange(0, 255)
        self.left_slider.valueChanged.connect(self.update_vibration)
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.left_slider)
        layout.addLayout(left_layout)
        
        # Sağ motor kontrolü
        right_layout = QHBoxLayout()
        right_label = QLabel('Sağ Motor:')
        self.right_slider = QSlider(Qt.Horizontal)
        self.right_slider.setRange(0, 255)
        self.right_slider.valueChanged.connect(self.update_vibration)
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.right_slider)
        layout.addLayout(right_layout)
    
    def create_led_controls(self, layout):
        # Grup başlığı
        led_label = QLabel('LED Işık Kontrolleri')
        led_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #3498db;
                margin-top: 15px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(led_label)
        
        # Renk seçici için container
        colors_layout = QHBoxLayout()
        colors_layout.setSpacing(10)
        
        # Özel renk seçici butonu
        custom_color_btn = QPushButton('Özel Renk Seç')
        custom_color_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                min-width: 150px;
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        custom_color_btn.clicked.connect(self.show_color_picker)
        colors_layout.addWidget(custom_color_btn)
        
        layout.addLayout(colors_layout)
    
    def check_controller(self):
        try:
            pygame.event.pump()
            joystick_count = pygame.joystick.get_count()
            
            if joystick_count > 0 and not self.is_connected:
                self.status_label.setText('Durum: Kontrolcü bulundu! Bağlanmak için butona tıklayın | Geliştirici: rtx4090')
                self.status_label.setStyleSheet("QLabel { color: orange; }")
            elif joystick_count == 0 and not self.is_connected:
                self.status_label.setText('Durum: Kontrolcü bulunamadı | Geliştirici: rtx4090')
                self.status_label.setStyleSheet("QLabel { color: red; }")
        except Exception as e:
            print(f"Kontrol hatası: {e}")
    
    def connect_controller(self):
        if not self.is_connected:
            if self.ds4.connect():
                self.is_connected = True
                self.connect_button.setText('Bağlantıyı Kes')
                
                # Şarj durumunu kontrol et ve göster
                battery_level, is_charging = self.ds4.get_battery_level()
                if battery_level is not None:
                    status_text = f'Durum: Bağlandı - DualShock 4 (Pil: %{battery_level * 10}'
                    if is_charging:
                        status_text += ' - Şarj Oluyor'
                    status_text += ') | Geliştirici: rtx4090'
                    self.status_label.setText(status_text)
                else:
                    self.status_label.setText('Durum: Bağlandı - DualShock 4 | Geliştirici: rtx4090')
                
                self.status_label.setStyleSheet("QLabel { color: green; }")
                
                # Test titreşimi
                self.ds4.set_vibration(128, 128)  # Orta şiddette titreşim
                time.sleep(0.5)
                self.ds4.set_vibration(0, 0)  # Titreşimi durdur
                
                QMessageBox.information(self, 'Başarılı', 'Kontrolcü başarıyla bağlandı!')
            else:
                QMessageBox.warning(self, 'Bağlantı Hatası', 
                    'Kontrolcü bulunamadı!\n\n'
                    '1. Kontrolcünün Bluetooth eşleştirmesi yapıldığından emin olun\n'
                    '2. PS + SHARE butonlarına basarak eşleştirme modunu tekrar deneyin\n'
                    '3. Windows Bluetooth ayarlarından bağlantıyı kontrol edin')
        else:
            self.ds4.disconnect()
            self.is_connected = False
            self.connect_button.setText('Kontrolcüye Bağlan')
            self.status_label.setText('Durum: Bağlı değil | Geliştirici: rtx4090')
            self.status_label.setStyleSheet("QLabel { color: red; }")
    
    def update_vibration(self):
        if self.is_connected:
            try:
                left = self.left_slider.value()
                right = self.right_slider.value()
                self.ds4.set_vibration(right, left)  # Sağ motor küçük, sol motor büyük
                print(f"Titreşim değerleri - Sol: {left}, Sağ: {right}")
            except Exception as e:
                print(f"Titreşim güncelleme hatası: {e}")
    
    def set_color(self, r, g, b):
        if self.is_connected:
            try:
                self.ds4.set_led_color(r, g, b)
            except Exception as e:
                print(f"LED renk değiştirme hatası: {e}")
    
    def vibration_pattern(self, pattern_name):
        if self.is_connected:
            try:
                self.ds4.vibration_pattern(pattern_name)
            except Exception as e:
                print(f"Titreşim modeli hatası: {e}")
    
    def show_color_picker(self):
        if self.is_connected:
            color = QColorDialog.getColor()
            if color.isValid():
                self.set_color(color.red(), color.green(), color.blue())
    
    def update_button_states(self):
        if self.is_connected:
            try:
                # Kontrolcüden veri oku
                data = self.ds4.device.read(64)
                if data:
                    # D-Pad durumları
                    dpad = data[5] & 0x0F
                    self.button_labels['↑'].setText(f'↑: {"🟩" if dpad == 0 or dpad == 1 or dpad == 7 else "⬛"}')
                    self.button_labels['→'].setText(f'→: {"🟩" if dpad == 1 or dpad == 2 or dpad == 3 else "⬛"}')
                    self.button_labels['↓'].setText(f'↓: {"🟩" if dpad == 3 or dpad == 4 or dpad == 5 else "⬛"}')
                    self.button_labels['←'].setText(f'←: {"🟩" if dpad == 5 or dpad == 6 or dpad == 7 else "⬛"}')
                    
                    # Ana tuşlar
                    buttons = data[5] >> 4
                    self.button_labels['□'].setText(f'□: {"🟩" if buttons & 0x1 else "⬛"}')
                    self.button_labels['×'].setText(f'×: {"🟩" if buttons & 0x2 else "⬛"}')
                    self.button_labels['○'].setText(f'○: {"🟩" if buttons & 0x4 else "⬛"}')
                    self.button_labels['△'].setText(f'△: {"🟩" if buttons & 0x8 else "⬛"}')
                    
                    # L1, R1, L2, R2
                    buttons2 = data[6]
                    self.button_labels['L1'].setText(f'L1: {"🟩" if buttons2 & 0x1 else "⬛"}')
                    self.button_labels['R1'].setText(f'R1: {"🟩" if buttons2 & 0x2 else "⬛"}')
                    self.button_labels['L2'].setText(f'L2: {"🟩" if buttons2 & 0x4 else "⬛"}')
                    self.button_labels['R2'].setText(f'R2: {"🟩" if buttons2 & 0x8 else "⬛"}')
                    
                    # Share, Options, L3, R3, PS, TouchPad
                    self.button_labels['SHARE'].setText(f'SHARE: {"🟩" if buttons2 & 0x10 else "⬛"}')
                    self.button_labels['OPTIONS'].setText(f'OPTIONS: {"🟩" if buttons2 & 0x20 else "⬛"}')
                    self.button_labels['L3'].setText(f'L3: {"🟩" if buttons2 & 0x40 else "⬛"}')
                    self.button_labels['R3'].setText(f'R3: {"🟩" if buttons2 & 0x80 else "⬛"}')
                    self.button_labels['PS'].setText(f'PS: {"🟩" if data[7] & 0x1 else "⬛"}')
                    self.button_labels['TOUCHPAD'].setText(f'TOUCHPAD: {"🟩" if data[7] & 0x2 else "⬛"}')
                    
                    # Analog çubuklar
                    lx = data[1] - 128
                    ly = data[2] - 128
                    rx = data[3] - 128
                    ry = data[4] - 128
                    
                    self.left_stick_label.setText(f'Sol Analog: X: {lx}, Y: {ly}')
                    self.right_stick_label.setText(f'Sağ Analog: X: {rx}, Y: {ry}')
            except Exception as e:
                print(f"Tuş durumu güncelleme hatası: {e}")
    
    def closeEvent(self, event):
        if self.is_connected:
            self.ds4.set_vibration(0, 0)  # Titreşimi durdur
            self.ds4.disconnect()
        pygame.quit()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Yükleme ekranını göster
    splash = LoadingScreen()
    splash.show()
    
    # Ana pencereyi oluştur ama henüz gösterme
    window = DS4ControlPanel()
    
    # Yükleme tamamlanana kadar bekle (5 saniye)
    start_time = time.time()
    while time.time() - start_time < 5:
        remaining = 5 - (time.time() - start_time)
        progress = min(100, ((5 - remaining) / 5) * 100)
        splash.progress = int(progress)
        app.processEvents()
        time.sleep(0.05)
    
    # Yükleme tamamlandığında ana pencereyi göster
    window.show()
    splash.finish(window)
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 