import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import ttkbootstrap as ttk


from PIL import Image, ImageTk

# Functions for the main application : 

def custom_print():
    print("I am being called")










ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue") 


# Setting main app along with the title and the iconf or the app : 
main_window  = ctk.CTk()
main_window.title("Batch Downloader")
# Setting up the icon later : 

# Setting default app size for the main app : 
main_window.geometry("800x600")
main_window.resizable(False , False)


## Constatns for the current window : 
WIDTH = 600
HEIGHT = main_window.winfo_height()




# main_window.wm_attributes('-toolwindow', True) # This makes the simple titleabr with only the close button and no minimize button 


### Defining the controls : 

website_url  = ctk.CTkEntry(master=main_window, width=640 , placeholder_text="Enter Website Url for Scrapping")
scrap_button  = ctk.CTkButton(master = main_window , text="Start Scrapping")

# Settings under this options frame 
options_frame  = ctk.CTkFrame(master=main_window , height = 50 , width = 780)
options_frame.pack_propagate(0)


video_check_var = ctk.StringVar(value="off")
audio_check_var  = ctk.StringVar(value = "off")



video_checkbox = ctk.CTkCheckBox(master = options_frame, text="Download Videos", command=custom_print,
                                     variable=video_check_var, onvalue="on", offvalue="off")

audio_checkbox  = ctk.CTkCheckBox(master = options_frame , text="Download Audio" , command=custom_print, variable=audio_check_var,
                                  onvalue="on" , offvalue="off")




### Placing the Controls : 
website_url.grid(row = 0  , column = 0 , padx = 5 , pady = 10)
scrap_button.grid(row = 0 , column = 1 , padx = 5 , pady = 10)

options_frame.grid( row = 1 , column  = 0 ,padx= 5 , pady = 5 , columnspan = 4)


video_checkbox.pack(side= 'left' , padx= 10)
audio_checkbox.pack(side = 'left' ,padx = 10)

# Running the main app: 
main_window.mainloop()