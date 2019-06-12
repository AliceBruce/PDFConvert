### installation
- pip install pdfplumber 
- pip install pdf2image
- brew install poppler

### usage
python ConvertPDF.py -s [source pdf dir] -t [target dir]


### dir
- source : pdf dir
- target
    - pdf_name 
        - cut images and txt
        - success : images and plists that are processed successfully
        - fail : images and plists that are not processed successfully
                   