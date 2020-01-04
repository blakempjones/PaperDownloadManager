# For GetCitation
import scholarly
import requests
from re import sub
# For file system monitoring
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
# For pdf reading
from tika import parser



def GetCitation(title: str, formatStr: str, bibFolder: str):
    
    # Forbidden characters
    forbiddenChars = '[:;]'
    
    # Currently only supports reference manager format
    formats = {"rm": ".ris"}
    
    query = scholarly.search_pubs_query(title)
    
    # Gets the link to the citation file
    citationLink = next(query).url_scholarbib
    
    citationLink = citationLink.split('=')
    
    # Adjusts the format to the requested one by changing the last query param
    citationLink[-1] = formatStr
    
    citationLink = "=".join(citationLink)
    
    # Makes a get request to download the reference
    citationText = requests.get(citationLink).text
    
    title = sub(forbiddenChars, '', title)
    
    # Writes the citation file to the bibliography folder using the title as the file name
    with open(bibFolder + "/" + title + formats[formatStr], "w+") as citationFile:
        
        citationFile.write(citationText)
    

def HandleNewFile(event):
    print(event)
    print("test")
    
 
def ExtractTitle(fullFileName):
    # Extracts the meta data and article content from the pdf
    articleFile = parser.from_file(fullFileName)
    
    # Can try and use the metadata field title (seems to be commonly used in 
    # more recently uploaded papers). Can also check the resource name field. To 
    # validate we can search the text and make sure that what we call the title
    # appears in the first two pages (new lines might be a problem). Otherwise,
    # can try more creative methods (find phd and take the text above it, try other
    # libraries that extract font size, first line over a certain size (new lines
    # are a problem again, at least in scientific reports))

if __name__ == "__main__":
    
    folderName = sys.argv[1]
    
    event_handler = PatternMatchingEventHandler(patterns = folderName + "*");
    event_handler.on_created = HandleNewFile;

    observer = Observer()
    observer.schedule(event_handler, "C:/Users/TheMainframe/Documents/Vitkin_Lab/Papers/")
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
    
    
    
    
    
    
    