import numpy as np
import glob
import time
from functools import partial
import sqlite3

from kivy.app import App
from kivy.lang import Builder

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.carousel import Carousel
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen

from kivy.clock import Clock
from kivy.graphics import Color
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.properties import ObjectProperty

# Configuration of app sceen on computer
from kivy.config import Config
Config.set('graphics', 'fullscreen', '0')
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')

# KIVY LANGUAGE
Builder.load_string('''
# ------------------- MENU ----------------------------- 
<Menu>:
    BoxLayout:
        orientation: 'vertical'
# Label: welcome
        Label:
            text: 'Welcome'
            font_size: 40
            bold: True
            italic: True
# Button for training game
        Button:
            text: 'Training'
            on_press: root.manager.current = 'game1'
            font_size: 40
            bold: True
            italic: True
# Button for labeling game
        Button:
            text: 'Labeling'
            on_press: root.manager.current = 'game2'
            font_size: 40
            bold: True
            italic: True
# Button for database
        Button:
            text: 'Database'
            on_press: root.manager.current = 'data'
            font_size: 40
            bold: True
            italic: True
# -------------------------------------------------------
# -------------- TRAINING GAME --------------------------
<Container1>:
# background color
    canvas.before:
        Color:
            rgba: 1, 1, 1, 0.85
        Rectangle:
            pos: self.pos
            size: self.size
# -------------------------------------------------------
# App Upper block (labels: points and result)
    BoxLayout:
        orientation: 'vertical'
        BoxLayout:
            size_hint_y: 1
# question to result label on btn press
            Label:
                size_hint_x: 5
                id: result
                text: 'Do images belong to one class?'
                font_size: 40
                color: [0, 0, 0, 1]
# points label
            Label:
                size_hint_x: 1
                id: points
                text: 'Score: 0'
                font_size: 30
                bold: True
                italic: True
                color: 0.15, 0.8, 0.3, 1
                canvas.before:
                    Color:
                        rgba: 0, 0, 0, 0.7
                    Rectangle:
                        pos: self.pos
                        size: self.size
# ------------------------------------------------------
# App middle block (images)
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 4
            Image:
                id: image1
                source: root.rand_image()
                allow_stretch: True
            Image:
                id: image2
                source: root.rand_image()
                allow_stretch: True
# images labels (shown after guess made)
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 1
            Label:
                id: imglab1
                text: ' '
                font_size: 35
                color: [1, 0, 1, 1]
                margin: 0
            Label:
                id: imglab2
                text: ' '
                font_size: 35
                color: [1, 0, 1, 1]
                margin: 0
# ------------------------------------------------------
# Buttons block (yes, hint, menu, no)
        BoxLayout:
            orientation: 'horizontal'
            size_hint_y: None
            size_hint_y: 1
# Button: yes
            Button:
                size_hint_x: 2
                id: btn1
                # background_color: 0, 0, 0, 0.6
                # min_state_time: 0.5
                text: 'Yes'
                font_size: 35
                on_release: root.btn_yes()
# Button: hint
            Button:
                size_hint_x: 1
                id: btnH
                text: 'Hint'
                font_size: 30
                on_release: root.btn_hint()
# Button: menu
            Button:
                size_hint_x: 1
                id: btn3
                text: 'Menu'
                font_size: 30
                on_release: root.manager.current = 'menu'
# Button: no
            Button:
                size_hint_x: 2
                id: btn2
                # background_color: 0, 0, 0, 0.6
                # min_state_time: 0.5
                text: 'No'
                font_size: 35
                on_release: root.btn_no()
# ------------------------------------------------------
# ------------------ LABELING GAME ---------------------
<Container2>:
    BoxLayout:
        orientation: 'vertical'
# Background color
        canvas.before:
            Color:
                rgba: 1, 1, 1, 0.85
            Rectangle:
                pos: self.pos
                size: self.size
        rows: 2
# ------------------------------------------------------
# Text block (question, class labels)
        BoxLayout:
            size_hint_y: 1
# Label direction class 1
            Label:
                id: label1
                text: '<-- Class 1'
                font_size: 40
                color: [1, 0, 1, 0.8]
# Label question
            Label:
                id: disp
                text: 'Which class?'
                font_size: 40
                height: 50
                color: [0, 0, 0, 1]
# Label direction class 2
            Label:
                id: label2
                text: 'Class 2 -->'
                font_size: 40
                height: 50
                color: [1, 0, 1, 0.8]
# ------------------------------------------------------
# Swiping image block (carousel)
        Carousel:
            size_hint_y: 5
            id: carousel
            index: 1
            on_index: root.write()
# Additional screen: label 2
            Label:
                id: left
                text: 'Label 2'
                font_size: 50
                color: 0, 0, 0, 1
                size: carousel.size
                center: self.center
# Image screen
            Image:
                id: image1
                source: root.rand_image()
                allow_stretch: True
                size: carousel.size
                center: self.center
# Additional screen: label 1
            Label:
                id: right
                text: 'Label 1'
                font_size: 50
                color: 0, 0, 0, 1
                size: carousel.size
                center: self.center
# ------------------------------------------------------
# Button menu
        Button:
            size_hint_y: 1
            id: btn5
            text: 'Menu'
            font_size: 30
            on_release: root.manager.current = 'menu'
# ------------------------------------------------------
# ----------------- DATABASE ---------------------------
<Database>:
    Button:
        id: datab
        text: 'Load data'
        font_size: 50
        on_press: root.readdata()

''')

# ---------- DATABASE ---------------------------------
# SQLite duombaze - prisijungimas
conn = sqlite3.connect('labelsdb.db') # or use :memory: to put it in RAM
cursor = conn.cursor()

# Lenteles sukurimas
cursor.execute("""CREATE TABLE IF NOT EXISTS labelstuff (imagename text, label text)""")

# ------------------------------------------------------
# Pradiniai kintamieji (img lists, ...)
label1 = glob.glob('label1/*')
label2 = glob.glob('label2/*')
new = glob.glob('new/*')
img_label = np.array([label1, label2])
known = label1 + label2
known_ch = np.random.choice(known, 6, replace = False)
new_labels = np.array([np.concatenate([known_ch, new])])

a = 0
k = 0
labeled = 0

l = 0
combo1 = 0
combo2 = 0
i = 0

# ------------------ MENU ---------------------------
class Menu(Screen):
    pass

# ---------------- TRAINING GAME ----------------------
class Container1(Screen):

# combo mirgsejimo ijungimas (nusiuncia i ReturnCombo22)
    def RetrunCombo11(self, *args):
        global combo1
        global i
        self.ids.result.color = [0, 0, 1, 1]
        self.ids.result.bold = True
        self.ids.result.italic = True
        self.ids.result.text = 'COMBO X{}'.format(combo1)
        sound = SoundLoader.load('garsas/combo.wav')
        sound.play()
        Clock.schedule_once(self.RetrunCombo22, 0.1)

# combo mirgsejimo isjungimas (nusiuncia i ReturnCombo11, po 11 karto perjungia i kita leveli)
    def RetrunCombo22(self, *args):
        global i
        self.ids.result.text = ' '
        i += 1
        if i < 11:
            Clock.schedule_once(self.RetrunCombo11, 0.1)
        else:
            Clock.schedule_once(self.LevelUp, 0.2)
            i = 0

# function generating random images from list
    def rand_image(self, img_label  = img_label, *args):
        l = np.random.choice(img_label.shape[0]) # 2 random images labels
        idx = np.random.choice(len(img_label[l])) # 2 random images index
        return img_label[l][idx]

# permeta i 2 zaidima
    def LevelUp(self, *args):
        global combo1
        sm.current = 'game2'
        popup = Popup(title='YOU REACHED THE COMBO ROUND', title_size = 50, size_hint=(None, None), size=(500, 200), title_align = 'center', title_color = [0, 1, 0, 1], content=Label(text='Keep it up! \n Can you beat the high score?', font_size = 30, halign = 'center', valign = 'middle'), background = 'clear.png', separator_color = [0, 1, 1, 0])
        popup.open()
        combo1  = 0

# hint popup on btn HINT press
    def btn_hint(self, *args):
        popup = Popup(title='HINT', title_size = 20, size_hint=(None, None), title_align = 'center', size=(400, 175), content=Label(text='Some cells are healthy. \n Others... Not so much :(', font_size = 30, halign = 'center', valign = 'middle'), separator_color = [1, 0, 0, 0])
        popup.open()

# looping 1 game
    def btn_next(self, *args):
        self.ids.btn1.disabled = False
        self.ids.btn2.disabled = False
        self.ids.result.color = [0, 0, 0, 1]
        self.ids.result.text = 'Do images belong to one class?'
        self.ids.image1.source = self.rand_image()
        self.ids.image2.source = self.rand_image()
        self.ids.imglab1.text = ' '
        self.ids.imglab2.text = ' '

# functional, which does a lot on btn YES press
    def btn_yes(self):
        global combo1
        self.ids.btn1.disabled = True
        self.ids.btn2.disabled = True
        x = np.array([int(self.ids.image1.source[5]), int(self.ids.image2.source[5])])
        if np.diff(x) == 0:
            self.ids.result.text = 'Correct!'
            self.ids.result.color = [0, 0, 1, 1]
            points = int(self.ids.points.text.lstrip('Score: '))
            points += 1
            combo1 += 1

            sound = SoundLoader.load('garsas/correct.wav')
            sound.play()

            # Clock.schedule_once(self.disable(), 0.5)

            self.ids.points.text = 'Score: {}'.format(points)

            if combo1 == 3:
                Clock.schedule_once(self.RetrunCombo11, 0.2)

        else:
            self.ids.result.text = 'Try again :('
            self.ids.result.color = [1, 0, 0, 1]
            points = int(self.ids.points.text.lstrip('Score: '))
            points -= 1
            combo1  = 0

            sound = SoundLoader.load('garsas/incorrect.wav')
            sound.play()

            # Clock.schedule_once(self.disable(), 0.5)

            self.ids.points.text = 'Score: {}'.format(points)
        self.ids.imglab1.text = 'Class {}'.format(x[0])   
        self.ids.imglab2.text = 'Class {}'.format(x[1])

        Clock.schedule_once(self.btn_next, 1.5)

# functional, which does a lot on btn NO press
    def btn_no(self):
        global combo1
        self.ids.btn1.disabled = True
        self.ids.btn2.disabled = True
        x = np.array([int(self.ids.image1.source[5]), int(self.ids.image2.source[5])])
        if np.diff(x) != 0:
            self.ids.result.text = 'Correct!'
            self.ids.result.color = [0, 0, 1, 1]
            points = int(self.ids.points.text.lstrip('Score: '))
            points += 1
            combo1 += 1

            sound = SoundLoader.load('garsas/correct.wav')
            sound.play()

            self.ids.points.text = 'Score: {}'.format(points)
            if combo1 == 3:
                Clock.schedule_once(self.RetrunCombo11, 0.2)
        else:
            self.ids.result.text = 'Try again :('
            self.ids.result.color = [1, 0, 0, 1]
            points = int(self.ids.points.text.lstrip('Score: '))
            points -= 1
            combo1 = 0

            sound = SoundLoader.load('garsas/incorrect.wav')
            sound.play()

            self.ids.points.text = 'Score: {}'.format(points)

        self.ids.imglab1.text = 'Class {}'.format(x[0])   
        self.ids.imglab2.text = 'Class {}'.format(x[1])
        Clock.schedule_once(self.btn_next, 1.5)

# ------------------------------------------------------
class Container2(Screen):
# function returning text to normal after combo
    def RetrunText(self, *args):
        global i
        i = 0
        self.ids.disp.color = [0, 0, 0, 1]
        self.ids.disp.bold = False
        self.ids.disp.italic = False
        self.ids.disp.font_size = 50
        self.ids.disp.text = 'Which class?'

# same as ReturnCombo11
    def RetrunCombo1(self, *args):
        global combo2
        global i
        self.ids.disp.color = [0, 0, 1, 1]
        self.ids.disp.bold = True
        self.ids.disp.italic = True
        self.ids.disp.font_size = 70
        self.ids.disp.text = 'COMBO X{}'.format(combo2)
        sound = SoundLoader.load('garsas/combo.wav')
        sound.play()
        Clock.schedule_once(self.RetrunCombo2, 0.1)

# same as ReturnCombo22, but without levels
    def RetrunCombo2(self, *args):
        global i
        self.ids.disp.text = ' '
        i += 1
        if i < 11:
            Clock.schedule_once(self.RetrunCombo1, 0.1)
        else:
            Clock.schedule_once(self.RetrunText, 0.2)
            i = 0

# function generating random images from list
    def rand_image(self, img_label  = img_label):
        global l
        l = np.random.choice(img_label.shape[0]) # 2 random images labels
        idx = np.random.choice(len(img_label[l])) # 2 random images index
        return img_label[l][idx]

# function on next swiping screen do a lot of stuff
    def write(self):

        global combo2
        global k
        global a
        global labeled
        sound = SoundLoader.load('garsas/swipe.wav')
        sound.play()
        if self.ids.carousel.index == 0:
            combo2 += 1
            # row = [self.ids.image1.source, 2]
            # with open('doc.csv', 'a') as f:
            #     f.write('{},{}\n'.format(self.ids.image1.source, 2))

            cursor.execute("INSERT INTO labelstuff VALUES(?, ?)", (str(self.ids.image1.source), "2"))
            conn.commit()

            if self.ids.image1.source[:5] == 'label':
                k += 1
                if int(self.ids.image1.source[5]) == 2:
                    a += 1
                    labeled += 1
                    if labeled == 2:
                        Clock.schedule_once(self.RetrunCombo1, 0.1)
                        labeled = 0
                        combo2 = 0
                else:
                    labeled = 0
                    combo2 = 0
                    sound = SoundLoader.load('garsas/combobreaker.wav')
                    sound.play()

            self.ids.image1.source = self.rand_image(img_label  = new_labels)
            self.ids.carousel.index = 1
            # print row
        if self.ids.carousel.index == 2:
            combo2 += 1
            # row = [self.ids.image1.source, 1]
            # with open('doc.csv', 'a') as f:
            #     f.write('{},{}\n'.format(self.ids.image1.source, 1))
            cursor.execute("INSERT INTO labelstuff VALUES(?, ?)", (str(self.ids.image1.source), "1"))
            conn.commit()


            if self.ids.image1.source[:5] == 'label':
                k += 1
                if int(self.ids.image1.source[5]) == 1:
                    a += 1
                    labeled += 1
                    if labeled == 2:
                        Clock.schedule_once(self.RetrunCombo1, 0.1)
                        labeled = 0
                        combo2 = 0
                else:
                    labeled = 0
                    combo2 = 0
                    sound = SoundLoader.load('garsas/combobreaker.wav')
                    sound.play()

            self.ids.image1.source = self.rand_image(img_label  = new_labels)
            self.ids.carousel.index = 1
            # print row


# ------------------- DATABASE VIEW -------------------------
class Database(Screen):
# function on btn press prints first 5 database lines
    def readdata(self):
        conn.close()
        db = sqlite3.connect('./labelsdb.db') # labelsdb.db - name of database
        cursor = db.cursor()
        cursor.execute("SELECT * FROM labelstuff")  # labelstuff - name of table
        s = cursor.fetchall() # read database to list?
        d = []
        for i in range(len(s)):
            d.append([s[i]])
        # print d
        self.ids.datab.text = '{} \n {} \n {} \n {} \n {}'.format(d[0], d[1], d[2], d[3], d[4])
        return self.ids.datab.text


# ----------------SCREEN MANAGER ----------------------------
sm = ScreenManager()
sm.add_widget(Menu(name='menu'))
sm.add_widget(Container1(name='game1'))
sm.add_widget(Container2(name='game2'))
sm.add_widget(Database(name='data'))

# --------------- APP RUN --------------------------
class MainApp(App):
    def build(self):
        self.title = 'Label Crush'
        return sm

if __name__ == "__main__":
    MainApp().run()