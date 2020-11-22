import PySimpleGUI as sg
import bs4 as bs
import urllib.request
import requests
import sys

# Define the window's contents
layout = [  [sg.Text("What's your Sitemap URL?")],
            [sg.Input()],
            [sg.Button('Go')] ]

# Create the window
window = sg.Window('Sitemap Crawler by Zeo Agency', layout)
                                                
# Display and interact with the Window
event, values = window.read()

# Do something with the information gathered
# headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'}
url = values[0]
sauce = urllib.request.urlopen(url).read()
soup = bs.BeautifulSoup(sauce, 'lxml')

# title için:
# print(soup.title.text)

sys.stdout = open('url-list.txt', 'w')

for link in soup.find_all('loc'):
	print(link.text)

# Finish up by removing from the screen
window.close()
  