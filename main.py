import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import ttkbootstrap as ttk


from PIL import Image, ImageTk

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue") 


# Setting main app along with the title and the iconf or the app : 
main_window  = ctk.CTk()
main_window.title("Batch Downloader")
# Setting up the icon later : 

# Setting default app size for the main app : 
main_window.geometry("800x600")
main_window.resizable(False , False)

# main_window.wm_attributes('-toolwindow', True) # This makes the simple titleabr with only the close button and no minimize button 


### Defining the controls : 
website_url  = ctk.CTkEntry(master=main_window)
scrap_button  = ctk.CTkButton(master = main_window , text="Start Scrapping")




### Placing the Controls : 
website_url.pack()
scrap_button.pack()




# Running the main app: 
main_window.mainloop()