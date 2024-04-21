import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

main_app = tk.Tk()


def clear_entry(action):
    url_entry.delete(0 ,END)

# Setting up the title and the icon for UI 
main_app.title("Batch Downloader")
main_app.geometry("560x130")
main_app.resizable(False , False)

# Setting up the controls for the main app : 
url_entry  = ttk.Entry(master = main_app , width=60)
scrapper_button  = ttk.Button(master=main_app , text="Start Scrapping" , width=23)
url_entry.insert('end' , "Enter Website Url")


options_frame  = ttk.LabelFrame(master=main_app ,text="Download Settings" , width=540 , height=60 )
options_frame.pack_propagate(0)


## Setting up checkboxes for the settings : 
videos_checkbutton  = ttk.Checkbutton(master=options_frame , text="Mp4 Videos" , bootstyle="square-toggle")
image_checkbutton  = ttk.Checkbutton(master=options_frame , text="Png Images" , bootstyle = "square_toggle")
documents_button  = ttk.Checkbutton(master=options_frame , text="PDF Files" , bootstyle  = "square-toggle")
music_button  = ttk.Checkbutton(master=options_frame , text="Mp3 Files" , bootstyle = "square-toggle")
zip_button  = ttk.Checkbutton(master=options_frame , text="Zip Files" , bootstyle = "square-toggle")



# Progress Bar for the main Url : 
progress_bar  = ttk.Progressbar(master=main_app , bootstyle = "success"  , value=1 , length=534)



## Binding the controls
url_entry.bind('<FocusIn>' , clear_entry)

# ----------------------------------- # Placing the controls :
url_entry.grid(row=0 , column=0 , padx=5 , pady=5 , rowspan=2)
scrapper_button.grid(row=0 ,column=2 ,padx=5 , pady = 5 )

options_frame.grid(row=3 , column = 0 , columnspan=5)
videos_checkbutton.pack(side="left" , padx=10)
image_checkbutton.pack(side="left" , padx=10)
documents_button.pack(side='left' , padx=10)
music_button.pack(side='left' , padx=10)
zip_button.pack(side='left' , padx=10)


progress_bar.place(x=10 , y = 110)

main_app.mainloop()