import numpy as np
import glob
import time
import sqlite3

from kivy.app import App
from kivy.lang import Builder

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.carousel import Carousel
from kivy.uix.popup import Popup
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.textinput import TextInput
from kivy.uix.scatter import Scatter
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen, RiseInTransition

from kivy.clock import Clock
from functools import partial
from kivy.graphics import Color
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.properties import ObjectProperty
from kivy.event import EventDispatcher

# Configuration of app sceen on computer
from kivy.config import Config
Config.set('graphics', 'fullscreen', '0')
Config.set('graphics', 'width', '800')
Config.set('graphics', 'height', '600')

# KIVY LANGUAGE
Builder.load_string('''
# ------------------- MENU ----------------------------- 
#:import np numpy

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
            text: 'Exit'
            on_press: root.exit()
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
# image (on press goes to zoom mode)
            Image_btn:
                id: image1
                source: app.rand_image()
                allow_stretch: True
                on_press: 
                    root.manager.current = 'zoom'
                    root.manager.get_screen('zoom').ids.zoom_img.source = self.source
# image (on press goes to zoom mode)
            Image_btn:
                id: image2
                source: app.rand_image()
                allow_stretch: True
                on_press: 
                    root.manager.current = 'zoom'
                    root.manager.get_screen('zoom').ids.zoom_img.source = self.source

# images labels (shown after guess made)
        BoxLayout:
            orientation: "horizontal"
            size_hint_y: 1
            Label:
                id: imglab1
                text: ' '
                font_size: 35
                color: 0.15, 0.8, 0.3, 1
                margin: 0
            Label:
                id: imglab2
                text: ' '
                font_size: 35
                color: 0.15, 0.8, 0.3, 1
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
                # min_state_time: 0.5
                text: 'Yes'
                font_size: 35
                background_normal: 'img/btn.jpg'
                background_down: 'img/btn_press.jpg'
                background_disabled_normal: 'img/btn_dis.jpg'
                border: 0,0,0,0
                color: 0,0,0,1
                on_release: root.btn_yes()
# Button: hint
            Button:
                size_hint_x: 1
                id: btnH
                text: 'Hint'
                font_size: 30
                background_normal: 'img/btn_black.jpg'
                background_down: 'img/btn_press.jpg'
                background_disabled_normal: 'img/btn_dis.jpg'
                border: 0,0,0,0
                on_release: root.btn_hint()
# Button: menu
            Button:
                size_hint_x: 1
                id: btn3
                text: 'Menu'
                font_size: 30
                background_normal: 'img/btn_black.jpg'
                background_down: 'img/btn_press.jpg'
                background_disabled_normal: 'img/btn_dis.jpg'
                border: 0,0,0,0
                on_release: root.manager.current = 'menu'
# Button: no
            Button:
                size_hint_x: 2
                id: btn2
                # min_state_time: 0.5
                text: 'No'
                font_size: 35
                background_normal: 'img/btn.jpg'
                background_down: 'img/btn_press.jpg'
                background_disabled_normal: 'img/btn_dis.jpg'
                border: 0,0,0,0
                color: 0,0,0,1
                on_release: root.btn_no()
# ------------------------------------------------------
# ------------------ LABELING GAME ---------------------
<Container2>:
    BoxLayout:
        orientation: 'vertical'
        rows: 2
# ------------------------------------------------------
# Swiping image block (carousel)
        Carousel:
            size_hint_y: 5
            id: carousel
            index: 1
            on_index: root.write()
# ADDITIONAL SCREEN: label 2
# Background color
            BoxLayout:
                canvas.before:
                    Color: 
                        rgba: 0.8, 0.9, 1, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
# Label 2
                Label:
                    id: left
                    text: 'Label 2'
                    font_size: 50
                    color: 0, 0, 0, 1
                    size: carousel.size
                    center: self.center
# IMAGE SCREEN
            BoxLayout:
                orientation: 'vertical'
# Background color
                id: c_canvas
                my_color1: 1, 0.8, 0.68, 1
                my_color2: 0.8, 0.9, 1, 1
                canvas.before:
                    Color:
                        rgba: self.my_color1
                    Rectangle:
                        # pos: self.pos
                        pos: self.center_x, self.y
                        size: self.width/2, self.height
                    Color:
                        rgba: self.my_color2
                    Rectangle:
                        pos: self.pos
                        size: self.width/2, self.height
                BoxLayout:
                    size_hint_y: 0.3        
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
# image for swiping
                Image:
                    id: image1
                    source: app.rand_image()
                    allow_stretch: True
                    size: carousel.size
                    center: self.center
# ADDITIONAL SCREEN: label 1
# Background color
            BoxLayout:
                canvas.before:
                    Color: 
                        rgba: 1, 0.8, 0.68, 1
                    Rectangle:
                        pos: self.pos
                        size: self.size
# Label 1
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
# ----------------- ZOOM MODE --------------------------
<Zoom>:
    BoxLayout:
        orientation: 'vertical'
        rows: 2
# movable image
        FloatLayout:
            Scatter:
                size_hint: None, None
                size: zoom_img.size
                Image:
                    id: zoom_img
                    size: self.parent.parent.size
                    pos: self.parent.parent.pos
                    allow_stretch: True
# button to return back to game
        Button:
            text: 'return'
            size_hint_y: 0.1
            font_size: 30
            background_normal: 'img/btn_black.jpg'
            background_down: 'img/btn_press.jpg'
            background_disabled_normal: 'img/btn_dis.jpg'
            border: 0,0,0,0
            # on_press: print(root.manager.get_screen('game1').ids.image1.source)
            on_release: 
                zoom_img.parent.rotation = 0
                zoom_img.parent.scale = 1
                zoom_img.parent.pos = 0, 0
                root.manager.current = 'game1'
''')

# ---------- DATABASE ---------------------------------
# SQLite duombaze - prisijungimas
conn = sqlite3.connect('labelsdb.db') # or use :memory: to put it in RAM
cursor = conn.cursor()

# Lenteles sukurimas
cursor.execute("""CREATE TABLE IF NOT EXISTS labelstuff (imagename text, label text)""")
# ------------------------------------------------------

# Pradiniai kintamieji (img lists)
label1 = glob.glob('label1/*')
label2 = glob.glob('label2/*')
new = glob.glob('new/*')
img_label = np.array([label1, label2])
known = label1 + label2
known_ch = np.random.choice(known, 6, replace = False)
new_labels = np.array([np.concatenate([known_ch, new])])

# ---------------------------------------------------------


# new widget: image with button behavior
class Image_btn(ButtonBehavior, Image):
    pass

# -------------- ZOOM MODE --------------------------
# zooming training game images
class Zoom(Screen):
    pass

# ------------------ MENU ---------------------------
class Menu(Screen):
# exit program
    def exit(self):
        App.get_running_app().stop()

# ---------------- TRAINING GAME ----------------------
class Container1(Screen):
# permeta i 2 zaidima
    def AfterCombo(self, *args):
        self.ids.result.color = [0, 0, 0, 1]
        self.ids.result.bold = False
        self.ids.result.italic = False
        self.ids.result.font_size = 40
        self.ids.result.text = 'Do images belong to one class?'
        MainApp.sm.current = 'game2'
        popup = Popup(title = 'YOU REACHED THE COMBO ROUND', title_size = 50, size_hint = (None, None),
                      size = (500, 200), title_align = 'center', title_color = [0, 1, 0, 1], 
                      content = Label(text='Keep it up! \n Can you beat the high score?', font_size = 30, 
                                      halign = 'center', valign = 'middle'), 
                      background = 'img/clear.png', separator_color = [0, 1, 1, 0])
        popup.open()

# hint popup on btn HINT press
    def btn_hint(self, *args):
        popup = Popup(title = 'HINT', title_size = 20, size_hint = (None, None), title_align = 'center', size = (400, 175),
                      content = Label(text = 'Some cells are healthy. \n Others... Not so much :(', 
                                      font_size = 30, halign = 'center', valign = 'middle'), 
                      separator_color = [1, 0, 0, 0])
        popup.open()

# looping training game (activates after pause on answer)
    def btn_next(self, *args):
        self.ids.btn1.disabled = False
        self.ids.btn2.disabled = False
        self.ids.result.color = [0, 0, 0, 1]
        self.ids.result.text = 'Do images belong to one class?'
        self.ids.image1.source = App.get_running_app().rand_image()
        self.ids.image2.source = App.get_running_app().rand_image()
        self.ids.imglab1.text = ' '
        self.ids.imglab2.text = ' '
# --------------------------------------------------------------------------

# functional, which does a lot on BTN YES PRESS
    def btn_yes(self):
        combo = App.get_running_app().combo
# isjungia mygtukus (yes, no)
        self.ids.btn1.disabled = True
        self.ids.btn2.disabled = True
# tikrina ar TEISINGAS ATSAKIMAS
        x = np.array([int(self.ids.image1.source[5]), int(self.ids.image2.source[5])])
        if np.diff(x) == 0:
            self.ids.result.text = 'Correct!'
            self.ids.result.color = [0, 0, 1, 1]
# skaiciuja score (+1) ir combo (+1) (jei teisingas)
            points = int(self.ids.points.text.lstrip('Score: '))
            points += 1
            combo += 1
            self.ids.points.text = 'Score: {}'.format(points)
# prideda garsa (jei teisingas)
            # sound = SoundLoader.load('garsas/correct.wav').play()
# ismeta kai combo (3) ir perjungia i kita zaidima (jei teisinga)
            if combo == 3:
                Clock.schedule_once(partial(App.get_running_app().Combo1, 'result'), 0.2)

# JEI ATSAKYMAS NETEISINGAS
        else:
            self.ids.result.text = 'Try again :('
            self.ids.result.color = [1, 0, 0, 1]
# skaiciuja score (-1) ir combo (=0) (jei neteisinga)
            points = int(self.ids.points.text.lstrip('Score: '))
            points -= 1
            combo  = 0
            self.ids.points.text = 'Score: {}'.format(points)
# prideda garsa (jei neteisingas)
            # sound = SoundLoader.load('garsas/incorrect.wav').play()
# end of atsakymu tikrinimo
# returns classes and activates btn_next (shows next 2 pictures)
        self.ids.imglab1.text = 'Class {}'.format(x[0])   
        self.ids.imglab2.text = 'Class {}'.format(x[1])
        App.get_running_app().combo = combo
        Clock.schedule_once(self.btn_next, 1.5)

# --------------------------------------------------------------------------

# functional, which does a lot on BTN NO PRESS
    def btn_no(self):
        combo = App.get_running_app().combo
# isjungia mygtukus (yes, no)
        self.ids.btn1.disabled = True
        self.ids.btn2.disabled = True
# tikrina ar TEISINGAS ATSAKIMAS
        x = np.array([int(self.ids.image1.source[5]), int(self.ids.image2.source[5])])
        if np.diff(x) != 0:
            self.ids.result.text = 'Correct!'
            self.ids.result.color = [0, 0, 1, 1]
# skaiciuja score (+1) ir combo (+1) (jei teisingas)
            points = int(self.ids.points.text.lstrip('Score: '))
            points += 1
            combo += 1
            self.ids.points.text = 'Score: {}'.format(points)
# prideda garsa (jei teisingas)
            # sound = SoundLoader.load('garsas/correct.wav').play()
# ismeta kai combo (3) ir perjungia i kita zaidima (jei teisinga)
            if combo == 3:
                Clock.schedule_once(partial(App.get_running_app().Combo1, 'result'), 0.2)

# JEI ATSAKYMAS NETEISINGAS
        else:
            self.ids.result.text = 'Try again :('
            self.ids.result.color = [1, 0, 0, 1]
# skaiciuja score (-1) ir combo (=0) (jei neteisinga)
            points = int(self.ids.points.text.lstrip('Score: '))
            points -= 1
            combo = 0
            self.ids.points.text = 'Score: {}'.format(points)
# prideda garsa (jei neteisingas)
            # sound = SoundLoader.load('garsas/incorrect.wav').play()
# end of atsakymu tikrinimo
# returns classes and activates btn_next (shows next 2 pictures)
        self.ids.imglab1.text = 'Class {}'.format(x[0])   
        self.ids.imglab2.text = 'Class {}'.format(x[1])
        App.get_running_app().combo = combo
        Clock.schedule_once(self.btn_next, 1.5)
# ------------------------------------------------------

# --------------------- LABELING GAME -------------------------------
class Container2(Screen):
# function returning text to normal after combo
    def AfterCombo(self, *args):
        self.ids.disp.color = [0, 0, 0, 1]
        self.ids.disp.bold = False
        self.ids.disp.italic = False
        self.ids.disp.font_size = 40
        self.ids.disp.text = 'Which class?'
     
# Play sound on swiping touch release
    def on_touch_up(self, touch):
        res =  super(Container2, self).on_touch_move(touch)
        if res:
            # sound = SoundLoader.load('./garsas/swipe.wav').play()
            pass
        return res

# function on next SWIPING screen do a lot of stuff
    def write(self):
        combo = App.get_running_app().combo
        k = App.get_running_app().k
        a = App.get_running_app().a
        labeled = App.get_running_app().labeled

# JEIGU LABEL SWIPINA KAIP 2
        if self.ids.carousel.index == 0:
    ## rasymas i csv faila (swiping 2)
            # row = [self.ids.image1.source, 2]
            # with open('doc.csv', 'a') as f:
            #     f.write('{},{}\n'.format(self.ids.image1.source, 2))
            # print row
# rasymas i sqlite duombaze (img name, label) (swiping 2)
            cursor.execute("INSERT INTO labelstuff VALUES(?, ?)", (str(self.ids.image1.source), "2"))
            conn.commit()

            combo += 1 # counts labeled img till combo 
# if img is already with known label (swiping 2)
            if self.ids.image1.source[:5] == 'label':
                k += 1 # kiek is viso buvo img
# tikrina ar zaidejas suleiblina teisingai (swiping 2, known label)
                if int(self.ids.image1.source[5]) == 2:
                    a += 1 # kiek is viso gerai suleiblinta
                    labeled += 1 # kiek gerai suleiblinta is eiles zinomu
# Jeigu 2 is zinomu suleiblino tesingai (swiping 2, known, correct)
                    if labeled == 2:
                        Clock.schedule_once(partial(App.get_running_app().Combo1, 'disp'), 0.2)
                        labeled = 0
# Jeigu suleiblina neteisingai (swiping 2, known)
                else:
                    labeled = 0
                    combo = 0
                    # sound = SoundLoader.load('garsas/combobreaker.wav').play()
# Looping Labeling game, change img and return center carousel screen (swiping 2)  
            self.ids.image1.source = App.get_running_app().rand_image(img_label = new_labels)
            self.ids.carousel.index = 1

# JEIGU LABEL SWIPINA KAIP 1
        if self.ids.carousel.index == 2:
    ## rasymas i csv faila (swiping 1)
            # row = [self.ids.image1.source, 1]
            # with open('doc.csv', 'a') as f:
            #     f.write('{},{}\n'.format(self.ids.image1.source, 1))
            # print row
# rasymas i sqlite duombaze (img name, label) (swiping 1)
            cursor.execute("INSERT INTO labelstuff VALUES(?, ?)", (str(self.ids.image1.source), "1"))
            conn.commit()

            combo += 1 # counts labeled img till combo 
# if img is already with known label (swiping 1)
            if self.ids.image1.source[:5] == 'label':
                k += 1 # kiek is viso buvo img
# tikrina ar zaidejas suleiblina teisingai (swiping 1, known label)
                if int(self.ids.image1.source[5]) == 1:
                    a += 1 # kiek is viso gerai suleiblinta
                    labeled += 1 # kiek gerai suleiblinta is eiles zinomu
# Jeigu 2 is zinomu suleiblino tesingai (swiping 1, known, correct)
                    if labeled == 2:
                        Clock.schedule_once(partial(App.get_running_app().Combo1, 'disp'), 0.2)
                        labeled = 0
# Jeigu suleiblina neteisingai (swiping 1, known)
                else:
                    labeled = 0
                    combo = 0
                    # sound = SoundLoader.load('garsas/combobreaker.wav').play()
# Looping Labeling game, change img and return center carousel screen (swiping 1)  
            self.ids.image1.source = App.get_running_app().rand_image(img_label = new_labels)
            self.ids.carousel.index = 1
# returning values
        App.get_running_app().combo = combo
        App.get_running_app().k = k
        App.get_running_app().a = a
        App.get_running_app().labeled = labeled
# --------------------------------------------------------------------------

# --------------- APP RUN --------------------------
class MainApp(App):
# screen manager
    sm = ScreenManager()
    i = 0 
    combo = 0
    a = 0
    k = 0
    labeled = 0
# -----------------------------------------------------------
# function generating random images from list
    def rand_image(self, img_label = img_label):
        l = np.random.choice(img_label.shape[0])
        idx = np.random.choice(len(img_label[l]))
        return img_label[l][idx]

# combo mirgsejimo ijungimas (nusiuncia i Combo2)
    def Combo1(self, idx, *largs):
        combo_idx = self.root.current_screen.ids[idx]
        combo_idx.color = [0, 0, 1, 1]
        combo_idx.bold = True
        combo_idx.italic = True
        combo_idx.font_size = 70
        combo_idx.text = 'COMBO X{}'.format(self.combo)
        # sound = SoundLoader.load('garsas/combo.wav').play()
        Clock.schedule_once(partial(self.Combo2, idx), 0.1)

# combo mirgsejimo isjungimas (nusiuncia i Combo1, po 11 karto baigiasi)
    def Combo2(self, idx, *largs):
        combo_idx = self.root.current_screen.ids[idx]
        combo_idx.text = ' '
        self.i += 1
        if self.i < 11:
            Clock.schedule_once(partial(self.Combo1, idx), 0.1)
        else:
            self.i = 0
            self.combo = 0
            Clock.schedule_once(self.root.current_screen.AfterCombo, 0.2) # Return: text to normal | swich game

# build app
    def build(self):
        self.title = 'Label Crush'
        MainApp.sm.add_widget(Menu(name='menu'))
        MainApp.sm.add_widget(Container1(name='game1'))
        MainApp.sm.add_widget(Container2(name='game2'))
        MainApp.sm.add_widget(Zoom(name='zoom'))
        return MainApp.sm

if __name__ == "__main__":
    MainApp().run()