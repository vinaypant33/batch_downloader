import tkinter as tk 
from tkinter import ttk 
import customtkinter as ctk 
import ttkbootstrap as ttkb

from tkinter import filedialog

window  = ctk.CTk()
window.title("Batch Downloader")
window.geometry("600x180")
window.resizable(False, False)


ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

#### Functions to be used in teh window 


def slider_value(value):
    depth_pages_label.configure(text = "Scrapping Depth : " + (str(round(value))))

def folder_selector_func():
    seelcted_folder.delete(0 , 100) # END is not working and will make the same for the delete 
    directory_path = filedialog.askdirectory()
    seelcted_folder.insert(0 , directory_path)


# setting up the controls using custom tkinter
website_url  = ctk.CTkEntry(master=window , placeholder_text="Enter Website URL for Scrapping" , width=440)
scrap_button  = ctk.CTkButton(master=window , text="Start Scrapping")

options_panel  = ctk.CTkFrame(master=window , width=window.winfo_width() - 10 , height=45)
options_panel.pack_propagate(0)

# Checkboxes for the main app : 
mp4_checkbox  = ctk.CTkCheckBox(master = options_panel , text="Mp4 Videos")
mp3_checkbox  = ctk.CTkCheckBox(master=options_panel , text="Mp3 Files")
png_checkbox = ctk.CTkCheckBox(master=options_panel , text="Png Images")
pdf_files  = ctk.CTkCheckBox(master=options_panel , text="Pdf Files")

# Make a spinbox for maing the depths of the pages :

depth_pages  = ctk.CTkSlider(master = options_panel, from_=0, to=10, command = slider_value ,number_of_steps = 10 )
depth_pages_label  = ctk.CTkLabel(master=options_panel , text="Scrapping Depth : " + str(round(depth_pages._output_value)))

folder_selector  = ctk.CTkButton(master=window , text="Select Folder"  ,command=folder_selector_func)
seelcted_folder = ctk.CTkEntry(master=window  , placeholder_text="Selected folder will appear here" , width=440) # In this the selected folder will be shown
# Status bar for the main app : it will show the current status for the scrapping and downloading : 
status_bar  = ctk.CTkLabel(master=window , text=":")

progress_bar  = ctk.CTkProgressBar(master=window  , width=585)
progress_bar.set(0)

website_url.place(x = 5 , y = 5 )
scrap_button.place(x = 450 , y  =5)
options_panel.place(x = 5 , y = 45)


mp4_checkbox.pack(side = 'left' , padx = 5 , pady = 5)
mp3_checkbox.pack(side = "left" , padx = 5 , pady = 5)
png_checkbox.pack(side= "left" , padx = 5 , pady = 5)
pdf_files.pack(side='left' , padx=5 ,pady =5)


depth_pages_label.pack()
depth_pages.pack()

folder_selector.place(x = 5 , y = 100)
seelcted_folder.place(x = 150 , y = 100)

progress_bar.place(x = 5 , y = 140)
status_bar.place(x = 5 , y = 150)


window.mainloop()



