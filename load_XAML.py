import os
from System.Windows.Markup import XamlReader, ParserContext
from System.IO import FileStream, FileMode
from System import Uri

def load_xaml(xaml_file):
    current_path = os.path.dirname(os.path.abspath(__file__))
    xaml_path = os.path.join(current_path, "ui", xaml_file)
    fs = FileStream(xaml_path, FileMode.Open)
    try:
        context = ParserContext()
        context.BaseUri = Uri(xaml_path)
        return XamlReader.Load(fs, context)
    finally:
        fs.Close()  
