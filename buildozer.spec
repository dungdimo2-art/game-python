[app]

# Tên ứng dụng
title = Game Vui

# Tên package Android
package.name = gamevui

# Tên miền package
package.domain = org.gamevui

# Thư mục chứa main.py
source.dir = .

# Các file được đưa vào APK
source.include_exts = py,png,jpg,jpeg,kv,atlas,mp3,wav,ogg,ttf

# Phiên bản
version = 1.0

# Thư viện Python cần thiết
requirements = python3,kivy

# Màn hình dọc
orientation = portrait

# Không bắt buộc toàn màn hình
fullscreen = 0

# Android API
android.api = 35

# Android tối thiểu
android.minapi = 23

# Chỉ build cho điện thoại Android 64-bit
android.archs = arm64-v8a

# Quyền Internet
android.permissions = INTERNET

# Không sử dụng icon riêng
icon.filename =

# Không sử dụng presplash
presplash.filename =

# Không sử dụng service
services =


[buildozer]

# Mức độ log
log_level = 2

# Cảnh báo khi chạy
warn_on_root = 1