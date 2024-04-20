import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import ttk


# Main window : 
main_window  = ctk.CTk()
main_window.title("Batch Downloader")

# Setting the theme for the main app : 
ctk.set_appearance_mode("light")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue") 

# App main geometry : 
main_window.geometry("800x600")
main_window.resizable(False , False)



# Defining custom functions : 
def custom_print(check_box_command):
    print(check_box_command)





# ------------------------------------------------ #

# seting up the controls for the main app : 
website_url  = ctk.CTkEntry(master=main_window, width=640 , placeholder_text="Enter Website Url for Scrapping")
scrap_button  = ctk.CTkButton(master = main_window , text="Start Scrapping")


# options frame :
options_frame  = ctk.CTkFrame(master=main_window , height = 50 , width = 780)
options_frame.pack_propagate(0)

# setting up string for the checkbox :

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


## setting up treeview for the main app : 

# scrollable frame : 

scrollable_frame = ctk.CTkScrollableFrame(main_window, width=752, height=480)



style = ttk.Style()
style.configure('Custom.Treeview', background='white', foreground='black', rowheight=20, font=('Arial', 10) )
style.configure('Custom.Treeview.Heading', font=('Arial', 10, 'bold'), background='black', foreground='skyblue')
style.map('Custom.Treeview', background=[('selected', 'skyblue')], foreground=[('selected', 'white')])
style.configure('Custom.Treeview', fieldbackground='black')




tree = ttk.Treeview(scrollable_frame , height=55 , columns = ("S.no" , "File Name" , "Status" ) , show='headings' , style='Custom.Treeview')


tree.heading("S.no" , text="S.No" )
tree.heading("File Name" , text="File Name")
tree.heading("Status" , text="Status")



# ------------------------------------------- #
# Packing the controls : 
website_url.grid(row = 0  , column = 0 , padx = 5 , pady = 10)
scrap_button.grid(row = 0 , column = 1 , padx = 5 , pady = 10)
options_frame.grid( row = 1 , column  = 0 ,padx= 5 , pady = 5 , columnspan = 4)

video_checkbox.pack(side= 'left' , padx= 10)
audio_checkbox.pack(side = 'left' ,padx = 10)
png_images_checkbox.pack(side = 'left'  ,padx = 10)


scrollable_frame.grid(row = 2 , column  = 0 , columnspan  = 5 ,  rowspan  = 5 , sticky = "NS")
tree.pack( expand=True , fill='both')


###

# for i in range(20):
#     tree.insert('',  'end' , values=("value " + str(i) , "vinay pant" , "hehe"))



# -------------------------------------------- # 

main_window.mainloop()