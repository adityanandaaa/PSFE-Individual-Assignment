# build_exe.py
import PyInstaller.__main__

PyInstaller.__main__.run([
    'app.py',
    '--onefile',
    '--windowed',
    '--add-data', 'data/currencies.json:data',
    '--name', 'FinancialHealthChecker'
])