import os, sys
import json
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import requests
import re
import zipfile
import shutil
import subprocess
from TOU import Ui_MainWindow
import time



class Window(QMainWindow, Ui_MainWindow):
    def __init__(self, uiFileName, baseUrl, compUrl, filename, *args, **kwargs):
        super(Window, self).__init__()  # Call the inherited classes __init__ method
        self.setupUi(self)
        self.filename = filename
        self.data = {}
        self.loadData()
        #uic.loadUi(uiFileName, self)  # Load the .ui file
        self.hAU = AmongUsMods(baseUrl, compUrl, self.progressBar, self.data) # hAU = handleAmongUs
        self.hAU.currentDirAU = self.data.get('currentDirAU')
        self.pushButton_2.setEnabled(False)
        self.show()
        self.connectSignalsSlots()
        self.lineEdit.setText('Sélectionner le chemin vers le dossier Among Us Steam' if self.hAU.currentDirAU==None or self.hAU.currentDirAU== '' else self.hAU.currentDirAU)
        # delay to display before auto update the game
        QTimer.singleShot(2000, lambda: self.updating())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Alt:
                self.plainTextEdit.appendPlainText('😁 Cet outil vous est mis à disposition par Thomas Giagnoli, avec tout son amour 😘')

    def loadData(self):
        ### load datas if exist
        if os.path.exists(self.filename):
            with open(self.filename, 'r+') as f:
                self.data = json.loads(f.read())
            self.lineEdit.setText(self.data.get('currentDirAU'))
        else:
            with open(self.filename, 'w') as f:
                f.write(json.dumps({}))

    def updateData(self, datas):
        self.data.update(datas)
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.data))

    def browseSlot(self):
        ### self Called when the user presses the Browse button
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.hAU.currentDirAU = QFileDialog.getExistingDirectory(self,'','C:\Program Files (x86)\Steam\steamapps\common', options=options)
        self.updateData({'currentDirAU':self.hAU.currentDirAU})
        self.lineEdit.setText(self.hAU.currentDirAU)
        self.updating()

    def updating(self):
        if self.hAU.currentDirAU != None:
            if 'Among Us' in self.hAU.currentDirAU:
                self.lineEdit.setStyleSheet("color: black;")
                self.plainTextEdit.appendPlainText('Répertoire Among Us trouvé ...')
                if self.hAU.createDestDir():
                    self.plainTextEdit.appendPlainText('Répertoire de destination crée ...')
                    self.plainTextEdit.appendPlainText('Téléchargement de la dernière version en cours ...')
                    self.hAU.download()
                else:
                    self.plainTextEdit.appendPlainText('Répertoire de destination existant ...')
                    self.plainTextEdit.appendPlainText('Version à jour ...')
                self.plainTextEdit.appendPlainText('Dernière version installée ...')
                self.hAU.hProgressBar.setValue(100)
                self.pushButton_2.setEnabled(True)
                self.plainTextEdit.appendPlainText('Jeu prêt à lancer ...')
            else:
                self.lineEdit.setStyleSheet("color: red;")
                self.plainTextEdit.appendPlainText('Répertoire Among Us introuvable ...')
                self.pushButton_2.setEnabled(False)

    def connectSignalsSlots(self):
        self.pushButton_2.clicked.connect(self.start)
        self.pushButton.clicked.connect(self.browseSlot)


    def start(self):
        self.pushButton_2.setEnabled(False)
        self.showMinimized()
        subprocess.call('"'+self.hAU.destFile+'/Among Us.exe"', shell=True)
        #os.system('"'+self.hAU.destFile+'/Among Us.exe"')
        self.showMaximized()
        self.pushButton_2.setEnabled(True)


class AmongUsMods:
    def __init__(self, baseUrl, compUrl, hProgressBar, *args, **kwargs):
        self.hProgressBar = hProgressBar
        self.baseUrl = baseUrl
        self.compUrl = compUrl
        self.currentDirAU = kwargs.get('currentDirAU')
        self.repoUrl = self.baseUrl+self.compUrl
        self.regex = '(\d+.\d+.\d+)'
        self.links = []
        self.ui_init = {}
        self.getRepositoryInfo()
        self.extractLinks()
        self.extractVersion()

    def getRepositoryInfo(self):
        self.resp = requests.get(self.repoUrl)
        if self.resp.status_code != 200:
            raise ConnectionError('HTTP error, got code : ' + str(self.resp.status_code))
        ### if a redirection occurred, redo the request on the right url
        if self.resp.url != self.repoUrl:
            print('Redirection from :\n' + str(self.repoUrl) + '\nto :\n' + str(self.resp.url) + '\n')
            self.resp = requests.get(self.resp.url)

    def extractLinks(self):
        ### split response content
        splitted_resp = self.resp.text.split('"')
        ### extract links contain .zip
        for line in splitted_resp:
            if '.zip' in line:
                if 'archive' not in line:
                    if '\n' not in line:
                        self.links.append(self.baseUrl + line)
        if len(self.links) != 1:
            raise ValueError('\n####################\nToo much links found\n####################\n')

    def extractVersion(self):
        self.version = re.search(self.regex, self.links[0]).group()
        return str(self.version)

    def createDestDir(self):
        self.destDir = '/'.join(self.currentDirAU.split('/')[:-1])
        self.destFile = self.destDir+'/AmongUs_TownOfUs_'+self.extractVersion()
        if os.path.exists(self.destFile):
            return False
            #shutil.rmtree(self.destFile)
        else:
            shutil.copytree(self.currentDirAU, self.destFile)
            return True

    def download(self):
        zipName = self.destDir+'/TownOfUs_' + self.version + '.zip'
        with open(zipName, 'wb') as f:
            resp = requests.get(self.links[0],stream=True)
            total_length = resp.headers.get('content-length')
            if total_length is None:
                f.write(resp.content)
            else:
                downloaded = 0
                total = int(total_length)
                for data in resp.iter_content(chunk_size=max(int(total / 1000), 1024 * 1024)):
                    downloaded += len(data)
                    f.write(data)
                    self.hProgressBar.setValue(int(100*(downloaded/total)))


        ### extract content
        with zipfile.ZipFile(zipName, 'r') as zip_ref:
            zip_ref.extractall(self.destFile)
        os.remove(zipName)


