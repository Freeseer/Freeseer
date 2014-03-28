#!/usr/bin/python
# -*- coding: utf-8 -*-

# freeseer - vga/presentation capture software
#
#  Copyright (C) 2011, 2014  Free and Open Source Software Learning Centre
#  http://fosslc.org
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# For support, questions, suggestions or any other inquiries, visit:
# http://wiki.github.com/Freeseer/freeseer/

'''
@author: Thanh Ha, Mia Kilborn
'''
from PyQt4.QtCore import QString
from PyQt4.QtCore import QTranslator
from PyQt4.QtCore import QUrl
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QDesktopServices
from PyQt4.QtGui import QGridLayout
from PyQt4.QtGui import QHBoxLayout
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QPixmap
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QWidget

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

from freeseer import NAME
from freeseer import URL
from freeseer import __version__
from freeseer.frontend.qtcommon import resource  # noqa

RECORD_BUTTON_ARTIST = u'Sekkyumu'
RECORD_BUTTON_LINK = u'http://sekkyumu.deviantart.com/'
HEADPHONES_ARTIST = u'Ben Fleming'
HEADPHONES_LINK = u'http://mediadesign.deviantart.com/'


class AboutWidget(QWidget):
    """ Common About Dialog for the Freeseer Project. This should be used for the
    about dialog when including one in GUIs.

    Layout:
    Logo  |  About Infos
          |  Buttons
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.setMinimumSize(100, 400)

        self.current_language = "en_US"
        self.uiTranslator = QTranslator()
        self.uiTranslator.load(":/languages/tr_en_US.qm")

        icon = QIcon()
        icon.addPixmap(QPixmap(_fromUtf8(":/freeseer/logo.png")), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        self.mainlayout = QGridLayout()
        self.setLayout(self.mainlayout)

        # Left top side of grid, Logo
        self.logo = QLabel("Logo")
        self.logo.setPixmap(QPixmap(_fromUtf8(":/freeseer/logo.png")))
        self.mainlayout.addWidget(self.logo, 0, 0)

        # Right top side of grid, Infos
        self.aboutInfo = QLabel("About Info", openExternalLinks=True)
        self.aboutInfo.setWordWrap(True)
        self.mainlayout.addWidget(self.aboutInfo, 0, 1)

        # Right bottom side of grid, Buttons
        self.buttonsLayout = QHBoxLayout()
        self.issueButton = QPushButton("Report an issue")
        self.docsButton = QPushButton("Freeseer documentation")
        self.contactButton = QPushButton("Contact us")
        self.buttonsLayout.insertWidget(0, self.docsButton)
        self.buttonsLayout.insertWidget(1, self.issueButton)
        self.buttonsLayout.insertWidget(2, self.contactButton)

        self.mainlayout.addLayout(self.buttonsLayout, 2, 1)

        self.connect(self.docsButton, SIGNAL('clicked()'), self.openDocsUrl)
        self.connect(self.issueButton, SIGNAL('clicked()'), self.openNewIssueUrl)
        self.connect(self.contactButton, SIGNAL('clicked()'), self.openContactUrl)

        self.retranslate()

    def retranslate(self, language=None):
        if language is not None:
            self.current_language = language

        self.uiTranslator.load(":/languages/tr_%s.qm" % self.current_language)

        #
        # Main Text
        #
        self.descriptionString = self.uiTranslator.translate("AboutDialog",
                    "Freeseer is a video capture utility capable of capturing presentations. It captures "
                    "video sources such as usb, firewire, or local desktop along with audio and mixes them "
                    "together to produce a video.")
        self.copyrightString = self.uiTranslator.translate("AboutDialog", 'Copyright (C) 2014 The Free and '
                    'Open Source Software Learning Centre')
        self.licenseTextString = self.uiTranslator.translate("AboutDialog", "Freeseer is licensed under the GPL "
                    "version 3. This software is provided 'as-is',without any express or implied warranty. In "
                    "no event will the authors be held liable for any damages arising from the use of this software.")

        self.aboutInfoString = u'<h1>' + NAME + u'</h1>' + \
            u'<br><b>' + self.uiTranslator.translate("AboutDialog", "Version") + ": " + __version__ + u'</b>' + \
            u'<p>' + self.descriptionString + u'</p>' + \
            u'<p>' + self.copyrightString + u'</p>' + \
            u'<p><a href="' + URL + u'">' + URL + u'</a></p>' \
            u'<p>' + self.licenseTextString + u'</p>' \
            u'<p>' + self.uiTranslator.translate("AboutDialog", "Record button graphics by") + \
            u': <a href="' + RECORD_BUTTON_LINK + u'">' + RECORD_BUTTON_ARTIST + u'</a></p>' \
            u'<p>' + self.uiTranslator.translate("AboutDialog", "Headphones graphics by") + \
            u': <a href="' + HEADPHONES_LINK + u'">' + HEADPHONES_ARTIST + u'</a></p><br>'

        self.aboutInfo.setText(self.aboutInfoString)
        # --- End Main Text

    def openDocsUrl(self):
        """Opens a link to the Freeseer online documentation"""
        url = QUrl("http://freeseer.readthedocs.org")
        QDesktopServices.openUrl(url)

    def openNewIssueUrl(self):
        """Opens a link to the Freeseer new issue page"""
        url = QUrl("https://github.com/Freeseer/freeseer/issues/new")
        QDesktopServices.openUrl(url)

    def openContactUrl(self):
        """Opens a link to Freeseer's contact information"""
        url = QUrl("http://freeseer.readthedocs.org/en/latest/contact.html")
        QDesktopServices.openUrl(url)

if __name__ == "__main__":
    import sys
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    main = AboutWidget()
    main.show()
    sys.exit(app.exec_())
