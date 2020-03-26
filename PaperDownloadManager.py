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
from PyPDF2 import PdfFileReader
# For pop up dialog
import ctypes
# For file management
from pathlib import Path
from os import rename
import re

def GetCitation(title: str, formatStr: str, bibFolder: str):
    
    # Forbidden characters
    forbiddenChars = '[:;]'
    
    # Currently only supports reference manager format
    formats = {"rm": ".ris"}

    query = scholarly.search_pubs_query("\"" + title + "\"")
    
    # Gets the link to the citation file
    try:
        citationLink = next(query).url_scholarbib
        
    except StopIteration:
        return ""
    
    citationLink = citationLink.split('=')
    
    # Adjusts the format to the requested one by changing the last query param
    citationLink[-1] = formatStr
    
    citationLink = "=".join(citationLink)
    
    # Makes a get request to download the reference
    citationText = requests.get(citationLink).text
    
    title = sub(forbiddenChars, '', title)
    
    # Filter out any problematic characters
    re.sub(r'[^\x00-\x7f]',r' ',citationText)
    
    # Writes the citation file to the bibliography folder using the title as the file name7
    with open(bibFolder + "/" + title + formats[formatStr], "w+", encoding='utf-8') as citationFile:
        
        citationFile.write(citationText)
    
    return citationText


def dialogBox(msg):
    box = ctypes.windll.user32.MessageBoxW
    box(None, msg, "Paper Download Manager", 0)
    

def HandleNewFile(event):

    # Filter any temp download files out
    if (event.src_path.split(".")[-1] == "crdownload"):
        return
        
    # Sleep to avoid trying to access the file while windows has a lock on it
    time.sleep(3)
    title = ExtractTitle(event.src_path)

    global bibFolder    
    citationText = GetCitation(title, "rm", bibFolder);
        
    # Citation was downloaded successfully
    if (citationText != ""):
        newTitle = "/".join(event.src_path.split("/")) + "/"
        # Rename the pdf to the title of the paper, matching the citation file
        if (event.src_path != newTitle):
            
            rename(event.src_path, newTitle)
        
        dialogBox("Successfully downloaded citation: \n" + citationText )
    else:
        dialogBox("No citation found for: " + event.src_path)
    
    
def HandleRenameFile(event):
        
    global bibFolder
    time.sleep(5)
    title = ExtractTitle(event.src_path)
    
    # Check if there is a bib file in the bib folder already.
    # Currently only uses .ris files
    # If file doesn't exist, pass event to new file handler
    if (not Path(bibFolder + title + ".ris").is_file()):
        HandleNewFile(event)
        
 
def ExtractTitle(fullFileName):
    
    title = ""
    # Extracts the meta data from the pdf
    with open(fullFileName, 'rb') as f:
        pdf = PdfFileReader(f)
        info = pdf.getDocumentInfo()
        if (("/Title") in info):
            title = info.title 
    
    # Get the part of the file path after the last slash
    filenameOnly = fullFileName.split("/")[-1]
    # Remove the extension
    filenameOnly = filenameOnly.split(".")[0]
    
    # Check if title exists in metadata, if not return filename as the title
    return title if (title != "") else filenameOnly
    
if __name__ == "__main__":
    
    if (len(sys.argv) != 3):
        
        raise EOFError("Paths to the folder to watch and biblipgraphy folder are required")
          
    folderName = sys.argv[1]
    
    global bibFolder 
    bibFolder = sys.argv[2]
    
    event_handler = PatternMatchingEventHandler(patterns = folderName + "*");
    event_handler.on_created = HandleNewFile;

    observer = Observer()
    observer.schedule(event_handler, folderName)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
    
    
    
    
    
    
    