# author : Thomas Giagnoli
# Date : 15.07.2021

from app import *


def main():
    baseUrl = 'https://github.com'
    compUrl = '/polusgg/Town-Of-Us/releases/latest'
    filename = 'TOU.log'
    ui_file_name = 'TOU.ui'


    ### launch UI
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    mainWin = Window(ui_file_name, baseUrl, compUrl, filename)
    sys.exit(app.exec())


if __name__ == '__main__':
    main()

