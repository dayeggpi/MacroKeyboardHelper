# MacroKeyboardHelper
Display images in notif area via HotKey to ease up usage of Macro Keyboard (Stream Deck etc)

In action (after pressing the Hotkey):

![Image](https://i.imgur.com/yjwsGYy.gif)

Settings:

![Image](https://i.imgur.com/TVqGjPT.png)

this is an example of images I did to help me use this DIY MacroKeyboard:

<img src="https://i.imgur.com/4ZWi2i2.jpeg" width="300">


## Purpose

When using a Macro Keyboard, or a Stream Deck, or a DIY version (https://legeeketsonmarteau.fr/stream-deck-diy/ for example), you might want to have a quick hint to remember what each buttons would do.
This software allows you to display these hint(s) as images, in the notification area, via a Hotkey.

## Usage

Create your image(s) of hints.
Place them in same folder as MacroKeyboardHelper (ensure that they are named 01.png, 02.png and so on).
Run MacroKeyboardHelper.
Go to systray area, right click, go to settings.
Click on "Set Hotkey" then press the combination of keys you wish to set as HotKey.
Adjust the Display time (in milliseconds).
Click save.
Next time you press your HotKey, your images will appear in the notification area (bottom right of your screen) for the given amount of time you set in "Display time".

## Settings.ini

```
[Settings]
hotkey = ctrl+shift+i
display_time = 3000
```

The following file will be created in the same folder as MacroKeyboardHelper.
You can edit it manually, or via the settings menu.
