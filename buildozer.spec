[app]

title = Game Vui
package.name = gamevui
package.domain = org.gamevui

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,mp3,wav,ogg,ttf

version = 1.0

requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23

android.archs = arm64-v8a

android.ndk = 27c

android.accept_sdk_license = True

android.permissions = INTERNET

icon.filename =
presplash.filename =

services =


[buildozer]

log_level = 2
warn_on_root = 1
