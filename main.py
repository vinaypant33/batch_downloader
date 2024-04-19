import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import ttkbootstrap as tttk

from ttkbootstrap.tableview import Tableview
from ttkbootstrap.constants import *

from PIL import Image, ImageTk



'''
pip install CTkTable
This workaround for adding the data in the table format 
'''

# Functions for the main application : 

def custom_print(check_box_command):
    print(check_box_command)



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

website_url  = ctk.CTkEntry(master=main_window, width=640 , placeholder_text="Enter Website Url for Scrapping")
scrap_button  = ctk.CTkButton(master = main_window , text="Start Scrapping")

# Settings under this options frame 
options_frame  = ctk.CTkFrame(master=main_window , height = 50 , width = 780)
options_frame.pack_propagate(0)


video_check_var = ctk.StringVar(value="off")
audio_check_var  = ctk.StringVar(value = "off")
png_images_check_var  = ctk.StringVar(value  = 'off')
jpeg_images_cehck_var  = ctk.StringVar(value= 'off')



video_checkbox = ctk.CTkCheckBox(master = options_frame, text="MP4 Videos", command=lambda  : custom_print("Mp4 Videos"),
                                     variable=video_check_var, onvalue="on", offvalue="off")

audio_checkbox  = ctk.CTkCheckBox(master = options_frame , text="Mp3 Audio" , command=lambda  : custom_print("Mp3 Audio"), variable=audio_check_var,
                                  onvalue="on" , offvalue="off")

png_images_checkbox  = ctk.CTkCheckBox(master=options_frame  , text="PNG Images" , command=lambda  :custom_print("Png Images"), variable=png_images_check_var,
                                       onvalue='on' , offvalue='off')




# Tabview for saving the file names and saving the data in the internal drive : 

# tabview  = ctk.CTkTabview(master=main_window , width = 760 , height= 470)
col_data  = [{
    "text" : "S.No" 
} , "Company Name"  ,{'text' : "User Count" , },]


# table_view  = Tableview(master=main_window , coldata=col_data , paginated=False , searchable=False , bootstyle=PRIMARY , stripecolor="green" )


### Placing the Controls : 
website_url.grid(row = 0  , column = 0 , padx = 5 , pady = 10)
scrap_button.grid(row = 0 , column = 1 , padx = 5 , pady = 10)
options_frame.grid( row = 1 , column  = 0 ,padx= 5 , pady = 5 , columnspan = 4)

video_checkbox.pack(side= 'left' , padx= 10)
audio_checkbox.pack(side = 'left' ,padx = 10)
png_images_checkbox.pack(side = 'left'  ,padx = 10)

# table_view.grid(row = 2 , column= 0 , columnspan= 5 , sticky="NS")


# tabview.grid(row = 2 , column = 0  , columnspan  = 5 , sticky  = "NS"




# Running the main app: 
main_window.mainloop()