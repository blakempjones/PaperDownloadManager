# For GetCitation
import scholarly
import requests
import re
# For file system monitoring
import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from watchdog import events as evt
# For pdf reading
from PyPDF2 import PdfFileReader
# For pop up dialog (Windows only)
import ctypes
# For file management
from pathlib import Path
from os import rename

def GetCitation(title: str, formatStr: str, bibFolder: str) -> str:
    '''
    Given the title of an article use the package Scholarly to query google 
    scholar for that article and return the reference file in the format 
    specified by the format string (currently only .ris is implemented). Write 
    the ris file to the bibFolder location.

    Parameters
    ----------
    title : str
        Title of the article.
    formatStr : str
        Identifier of the filetype for the reference (only ris is implemented).
    bibFolder : str
        Folder to write the reference file to.

    Returns
    -------
    str
        Returns the text of the reference file.

    '''
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
    # Filter out any problematic characters
    citationText = re.sub(r'[^\x00-\x7f]',r' ', citationText)
    
    # Writes the citation file to the bibliography folder using the title as the file name7
    with open(bibFolder + "/" + title + formats[formatStr], "w+", encoding='utf-8') as citationFile:
        
        citationFile.write(citationText)
    
    return citationText


def dialogBox(msg: str) -> None:
    '''
    Opens a Windows dialog box and displays msg.

    Parameters
    ----------
    msg : str
        Text to display.

    '''
    box = ctypes.windll.user32.MessageBoxW
    box(None, msg, "Paper Download Manager", 0)
    

def HandleNewFile(event: evt.FileCreatedEvent) -> None:
    '''
    Event handler for a new file in the watched folder. Attempts to get the 
    title from the metadata. If no title is found it uses the filename. The 
    title is used to query Google Scholar and download the reference file. If 
    sucessful, the reference file is written to the bibFolder and the citation 
    is displayed in a dialog box. If the paper cannot be found, the user is 
    notified by a dialog box.

    Parameters
    ----------
    event : evt.FileCreatedEvent
        Watchdog filesystem event.


    '''
    print(event)
    # Filter out any temp download files
    if (event.src_path.split(".")[-1] == "crdownload"):
        return
        
    # Sleep to avoid trying to access the file while windows has a lock on it
    time.sleep(3)
    title = ExtractTitle(event.src_path)

    global bibFolder    
    citationText = GetCitation(title, "rm", bibFolder);
        
    # Citation was downloaded successfully
    if (citationText != ""):
        newTitle = "/".join(event.src_path.split("/")[:-1]) + "/" + title + ".pdf"
        # Rename the pdf to the title of the paper, matching the citation file
        if (event.src_path != newTitle):
            rename(event.src_path, newTitle)
        dialogBox("Successfully downloaded citation: \n" + citationText )
    else:
        dialogBox("No citation found for: " + event.src_path)
    
    
def HandleRenameFile(event: evt.FileMovedEvent) -> None:
    '''
    Event handler for a renamed file in the watched folder. Checks to see
    if the new name is the name of an existing reference file, if not it raises
    a new file event which is caught by HandleNewFile.

    Parameters
    ----------
    event : evt.FileMovedEvent
        DESCRIPTION.


    '''
    print(event)
    # Filter out any temp download files
    if (event.src_path.split(".")[-1] == "crdownload"):
        return
    
    global bibFolder
    time.sleep(5)
    title = ExtractTitle(event.dest_path)
    
    # Check if there is a bib file in the bib folder already.
    # Currently only uses .ris files
    # If file doesn't exist, pass event to new file handler
    if (not Path(bibFolder + title + ".ris").is_file()):
        HandleNewFile(evt.FileCreatedEvent(event.dest_path))
    # Ris file exists, rename pdf file to the same name as the ris file
    else: 
        newTitle = "/".join(event.dest_path.split("/")[:-1]) + "/" + title + ".pdf"
        rename(event.dest_path, newTitle)
        
 
def ExtractTitle(fullFileName: str) -> str:
    '''
    Given a filepath to an article pdf, opens the pdf and reads the 
    metadata for a title. If none found it uses the filename of the pdf as the 
    title for the paper.

    Parameters
    ----------
    fullFileName : str
        Path to an article pdf.

    Returns
    -------
    str
        The title as found in the metadata or the filename of the pdf.

    '''
    title = ""
    # Extracts the meta data from the pdf
    with open(fullFileName, 'rb') as f:
        pdf = PdfFileReader(f)
        info = pdf.getDocumentInfo()
        if (("/Title") in info):
            title = info.title 
    
    # Check if title exists in metadata, if not return filename as the title
    if (title == ""):
        title = fullFileName.split("/")[-1]
        title = title.split(".")[0]        
                
    # Forbidden characters
    forbiddenChars = '[:;]'
     # Filter out any problematic characters
    title = re.sub(forbiddenChars,'', title)
    return title
    

if __name__ == "__main__":
    
    if (len(sys.argv) != 3):
        raise EOFError("Paths to the folder to watch and biblipgraphy folder are required." +
            " Call this file by: \n PaperDownloadManager.py" + 
            " path_to_folder_to_watch path_to_bibliography_folder")
          
    folderName = sys.argv[1]
    
    global bibFolder 
    bibFolder = sys.argv[2]
    
    # Set event handlers
    event_handler = PatternMatchingEventHandler(patterns = folderName + "*");
    event_handler.on_created = HandleNewFile;
    event_handler.on_moved = HandleRenameFile
    
    # Run watchdog observer for the specified folders
    observer = Observer()
    observer.schedule(event_handler, folderName)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    
    
    
    
    
    
    
    