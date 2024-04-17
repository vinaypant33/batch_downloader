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


## Constatns for the current window : 
WIDTH = 600
HEIGHT = main_window.winfo_height()




# main_window.wm_attributes('-toolwindow', True) # This makes the simple titleabr with only the close button and no minimize button 


### Defining the controls : 
upper_panel  = tk.PanedWindow(master = main_window , width=WIDTH)
website_url  = ctk.CTkEntry(master=upper_panel)
scrap_button  = ctk.CTkButton(master = upper_panel , text="Start Scrapping")

middle_panel  =tk.PanedWindow(master=main_window , width=WIDTH , background="green")




### Placing the Controls : 
upper_panel.pack(side="top" , expand='y', padx=2 , pady=2)
website_url.pack()
scrap_button.pack()




# Running the main app: 
main_window.mainloop()