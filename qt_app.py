from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, 
                           QFrame, QFormLayout, QComboBox, QTimeEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
import sys
import schedule
from datetime import datetime, timedelta, time
from src.scheduler import job, scheduler_thread  # Update import to use src.scheduler
from src.config_manager import load_config, update_config  # Update import
from src.shared_state import stop_event  # Update import
import os

class SchedulerThread(QThread):
    status_update = pyqtSignal(str)

    def __init__(self, config):
        super().__init__()
        self.config = config

    def run(self):
        scheduler_thread(
            first_name=self.config["user"]["first_name"],
            last_name=self.config["user"]["last_name"],
            email=self.config["user"]["email"],
            skip_check=self.config["settings"].get("skip_check", False)
        )

class ModernAutomatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = load_config()
        self.scheduler_thread = None
        self.init_ui()
        
    def init_ui(self):
        # Add window icon
        self.setWindowIcon(QIcon('icon.png'))  # Add an icon file to your project
        
        self.setWindowTitle('Food Pantry Slot Booking')
        self.setMinimumWidth(500)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f6fa;
            }
            QLabel {
                color: #2c3e50;
                font-size: 13px;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #dcdde1;
                border-radius: 5px;
                background-color: white;
                font-size: 13px;
            }
            QCheckBox {
                color: #2c3e50;
                spacing: 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2573a7;
            }
            QFrame#section {
                background-color: white;
                border-radius: 10px;
                padding: 20px;
                border: 1px solid #dcdde1;
            }
            QLabel#header {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            }
            QLabel#status {
                font-size: 14px;
                color: #7f8c8d;
            }
        """)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # User Information Section
        user_frame = QFrame()
        user_frame.setObjectName("section")
        user_layout = QFormLayout()
        
        header = QLabel("User Information")
        header.setObjectName("header")
        user_layout.addRow(header)
        
        self.first_name = QLineEdit(self.config["user"]["first_name"])
        self.last_name = QLineEdit(self.config["user"]["last_name"])
        self.email = QLineEdit(self.config["user"]["email"])
        
        user_layout.addRow("First Name:", self.first_name)
        user_layout.addRow("Last Name:", self.last_name)
        user_layout.addRow("Email:", self.email)
        user_frame.setLayout(user_layout)
        main_layout.addWidget(user_frame)

        # Settings Section
        settings_frame = QFrame()
        settings_frame.setObjectName("section")
        settings_layout = QVBoxLayout()
        
        settings_header = QLabel("Settings")
        settings_header.setObjectName("header")
        settings_layout.addWidget(settings_header)
        
        self.headless = QCheckBox("Run in Headless Mode")
        self.stop_after_success = QCheckBox("Stop After Successful Registration")
        self.skip_check = QCheckBox("Skip URL Check (Direct SignUpGenius URL)")
        
        self.headless.setChecked(self.config["settings"]["headless"])
        self.stop_after_success.setChecked(self.config["settings"]["stop_after_success"])
        self.skip_check.setChecked(self.config["settings"].get("skip_check", False))
        
        settings_layout.addWidget(self.headless)
        settings_layout.addWidget(self.stop_after_success)
        settings_layout.addWidget(self.skip_check)
        settings_frame.setLayout(settings_layout)
        main_layout.addWidget(settings_frame)

        # Schedule Settings Section
        schedule_frame = QFrame()
        schedule_frame.setObjectName("section")
        schedule_layout = QFormLayout()
        
        schedule_header = QLabel("Schedule Settings")
        schedule_header.setObjectName("header")
        schedule_layout.addRow(schedule_header)
        
        # Day of week combo box
        self.day_combo = QComboBox()
        self.day_combo.addItems(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
        self.day_combo.setCurrentIndex(self.config["schedule"].get("day_of_week", 0))
        schedule_layout.addRow("Check Day:", self.day_combo)
        
        # Time window inputs
        self.start_time = QTimeEdit()
        self.end_time = QTimeEdit()
        
        # Get times from config or use defaults
        start_time = datetime.strptime(
            self.config["schedule"].get("start_time", "09:30"), 
            "%H:%M"
        ).time()
        end_time = datetime.strptime(
            self.config["schedule"].get("end_time", "10:00"), 
            "%H:%M"
        ).time()
        
        self.start_time.setTime(QTime(start_time.hour, start_time.minute))
        self.end_time.setTime(QTime(end_time.hour, end_time.minute))
        
        schedule_layout.addRow("Start Time:", self.start_time)
        schedule_layout.addRow("End Time:", self.end_time)
        
        schedule_frame.setLayout(schedule_layout)
        main_layout.addWidget(schedule_frame)

        # Status Section
        status_frame = QFrame()
        status_frame.setObjectName("section")
        status_layout = QVBoxLayout()
        
        status_header = QLabel("Status")
        status_header.setObjectName("header")
        status_layout.addWidget(status_header)
        
        self.status_label = QLabel("Ready to start automation")
        self.status_label.setObjectName("status")
        status_layout.addWidget(self.status_label)
        
        next_run = self.get_next_run_text()
        self.next_run_label = QLabel(next_run)
        self.next_run_label.setObjectName("status")
        status_layout.addWidget(self.next_run_label)
        
        status_frame.setLayout(status_layout)
        main_layout.addWidget(status_frame)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Configuration")
        start_btn = QPushButton("Start Automation")
        stop_btn = QPushButton("Stop Automation")
        
        save_btn.clicked.connect(self.save_config)
        start_btn.clicked.connect(self.start_automation)
        stop_btn.clicked.connect(self.stop_automation)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(start_btn)
        button_layout.addWidget(stop_btn)
        main_layout.addLayout(button_layout)

    def get_next_run_text(self):
        """Get text showing next scheduled run based on configured day and time"""
        today = datetime.now()
        config_day = self.config["schedule"].get("day_of_week", 0)
        days_ahead = config_day - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_date = today + timedelta(days=days_ahead)
        start_time = self.config["schedule"].get("start_time", "09:30")
        return f"Next run: {next_date.strftime('%Y-%m-%d')} at {start_time}"

    def get_next_monday(self):
        today = datetime.now()
        days_ahead = 7 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return today + timedelta(days_ahead)

    def save_config(self):
        try:
            update_config(
                first_name=self.first_name.text().strip(),
                last_name=self.last_name.text().strip(),
                email=self.email.text().strip(),
                headless=self.headless.isChecked(),
                stop_after_success=self.stop_after_success.isChecked(),
                skip_check=self.skip_check.isChecked(),
                day_of_week=self.day_combo.currentIndex(),
                start_time=self.start_time.time().toString("HH:mm"),
                end_time=self.end_time.time().toString("HH:mm")
            )
            self.status_label.setText("Configuration saved successfully!")
        except Exception as e:
            self.status_label.setText(f"Error saving configuration: {str(e)}")

    def start_automation(self):
        if not all([self.first_name.text(), self.last_name.text(), self.email.text()]):
            self.status_label.setText("Error: Please fill in all user information!")
            return
            
        self.save_config()
        stop_event.clear()
        
        config = load_config()
        
        # Run immediately first
        job(
            first_name=config["user"]["first_name"],
            last_name=config["user"]["last_name"],
            email=config["user"]["email"],
            skip_check=config["settings"].get("skip_check", False),
            headless=config["settings"]["headless"]  # Pass headless setting
        )
        
        if not stop_event.is_set():
            self.scheduler_thread = SchedulerThread(config)
            self.scheduler_thread.start()
            self.status_label.setText("Automation running")

    def stop_automation(self):
        stop_event.set()
        if self.scheduler_thread:
            self.scheduler_thread.quit()
            self.scheduler_thread.wait()
        self.status_label.setText("Automation stopped")

    def closeEvent(self, event):
        self.stop_automation()
        event.accept()

def main():
    # Set environment variables to handle composition issues
    os.environ["QT_QPA_PLATFORM"] = "windows:darkmode=2"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
    
        # Initialize application
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    
    app = QApplication(sys.argv)
    # Use Qt6 compatible high DPI settings
    app.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    window = ModernAutomatorGUI()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
