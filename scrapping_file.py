import os
import requests as rq

from bs4 import BeautifulSoup

## Steps for the software 
'''
class for the main app which can be imported and then can be used for the scrapping 
Url and depth of the page is to be mentioned in the class 
after the number of links and what to scrap is to be defined in the class and each function to be defined for the scrapping
cehck by if else statement weather the scrapping of the video etc is done 

make the scrapper and a list which contains the list of the string and then savbe the temporary data in the text file and read the fle and start downloading it 


'''


class Scrapper():

    def __init__(self , url , depth ) -> None:
        self.url  = url
        self.site_depth  = depth

    
    # Function to visit the website and get the text : 
    def get_text(self):
        self.url_visit  = rq.get(self.url)
        url_response = self.url_visit.text
        with open (url_response , 'r') as html_file:
            content  = html_file.read()
            soup = BeautifulSoup(content , 'lxml')
            return soup.prettify()


    