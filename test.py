try:
    from flask import Flask
    print("Flask установлен успешно!")
except ImportError as e:
    print("Flask НЕ установлен:", e)