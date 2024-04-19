import customtkinter as ctk
from PIL import Image, ImageTk
from tkinter import ttk





# Functions for the main application : 

def custom_print(check_box_command):
    print(check_box_command)



ctk.set_appearance_mode("light")  # Modes: system (default), light, dark
ctk.set_default_color_theme("green") 


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

style1 = ttk.Style()
style1.configure("my.style", background="green")




### Placing the Controls : 
website_url.grid(row = 0  , column = 0 , padx = 5 , pady = 10)
scrap_button.grid(row = 0 , column = 1 , padx = 5 , pady = 10)
options_frame.grid( row = 1 , column  = 0 ,padx= 5 , pady = 5 , columnspan = 4)

video_checkbox.pack(side= 'left' , padx= 10)
audio_checkbox.pack(side = 'left' ,padx = 10)
png_images_checkbox.pack(side = 'left'  ,padx = 10)




scrollable_frame = ctk.CTkScrollableFrame(main_window, width=752, height=480)
scrollable_frame.grid(row = 2 , column  = 0 , columnspan  = 5 ,  rowspan  = 5 , sticky = "NS")


style = ttk.Style()
style.configure('Custom.Treeview', background='lightblue', foreground='black', rowheight=30)


tree = ttk.Treeview(scrollable_frame , height=25 , columns = ("S.no" , "File Name" , "Status") , show='headings' , style='custom.Treeview')

tree.heading('S.no' , text="S.no")
tree.heading('#1' , text="File Name")
tree.heading('#2' , text = "Status")
tree.heading('#3' , text = "Finished Date")


tree.tag_configure('custom.Treeview' , background='black')
tree.pack( expand=True , fill='both')

# for i in range(100):
#     tree.insert('' ,'end' , values = ('values1' , 'value2' , 'values 3' , 'values 4'))



# Running the main app: 
main_window.mainloop()