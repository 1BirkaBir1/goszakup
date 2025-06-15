from setuptools import setup

APP = ['main.py']  # замените на имя вашего .py файла
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['pandas', 'selenium', 'openpyxl', 'webdriver_manager'],
}

setup(
    app=APP,
    name="ПарсерЗакупок",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
