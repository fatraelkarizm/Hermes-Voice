APP_STYLE = """
* {
    color: #f2f2f2;
    font-family: Consolas, "Courier New", monospace;
    letter-spacing: 0px;
}

QMainWindow {
    background: transparent;
}

QFrame#Shell {
    background: #050607;
    border: 1px solid #a8a8a8;
}

QFrame#Panel {
    background: #07090a;
    border: 1px solid #6f7478;
}

QLabel#Title {
    font-size: 25px;
    font-weight: 700;
}

QLabel#Subtitle {
    color: #c2c2c2;
    font-size: 11px;
    font-weight: 600;
}

QLabel#Clock {
    color: #f7f7f7;
    font-size: 14px;
    font-weight: 700;
}

QLabel#SectionTitle {
    color: #d8d8d8;
    font-size: 11px;
    font-weight: 700;
}

QLabel#Status {
    color: #ffffff;
    font-size: 14px;
    font-weight: 700;
}

QLabel#Footer {
    color: #a8a8a8;
    font-size: 11px;
    font-weight: 600;
}

QPushButton {
    background: #090b0c;
    border: 1px solid #81878b;
    color: #f2f2f2;
    min-height: 28px;
    padding: 4px 10px;
}

QPushButton:hover {
    background: #111518;
    border-color: #ffffff;
}

QPushButton:pressed {
    background: #1b2023;
}

QPushButton:disabled {
    color: #777;
    border-color: #444;
}

QPushButton#WindowButton {
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
    font-size: 18px;
    font-weight: 700;
    padding: 0px;
}

QTextEdit, QPlainTextEdit, QLineEdit {
    background: #030405;
    border: 1px solid #34383b;
    color: #ffffff;
    selection-background-color: #ffffff;
    selection-color: #050607;
}

QTextEdit, QPlainTextEdit {
    padding: 10px;
    font-size: 12px;
}

QLineEdit {
    min-height: 34px;
    padding: 4px 8px;
    font-size: 12px;
}
"""

