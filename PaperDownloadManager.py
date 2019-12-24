import scholarly
import requests
import watchdog


def GetCitation(title: str, formatStr: str, bibFolder: str):
    
    # Currently only supports reference manager format
    formats = {"rm": ".ris"}
    
    query = scholarly.search_pubs_query(title)
    
    citationLink = next(query).url_scholarbib
    
    citationLink = citationLink.split('=')
    
    citationLink[-1] = formatStr
    
    citationLink = citationLink.join("=")
    
    citationText = requests.get(citationLink).text
    
    with open(bibFolder + "/" + title + formats[formatStr], "w") as citationFile:
        
        citationFile.write(citationText)
    


    
    
    
    
    
    
    
    
    