#!/usr/bin/env python3
import npyscreen

class App(npyscreen.StandardApp):
    def onStart(self):
        self.addForm("MAIN", MainForm, name="Player UI")

class DeckBox(npyscreen.BoxTitle):
    _contained_widget = npyscreen.MultiLineEdit

class MainForm(npyscreen.Form):
    def create(self):
        # self.title = self.add(npyscreen.TitleText, name="Deck", value="")
        self.deck = self.add(DeckBox, footer="Not editable", editable=False, )
        self.deck.value="coucou noe"

MyApp = App()
MyApp.run()