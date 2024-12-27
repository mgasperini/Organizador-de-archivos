import os
import datetime
from PIL import Image

class FileMetadata:
    @staticmethod
    def get_file_date(file_path):
        if file_path.lower().endswith(('.jpg', '.jpeg')):
            try:
                with Image.open(file_path) as img:
                    exif = img.getexif()
                    if exif:
                        for tag_id in (36867, 306, 36868):
                            if tag_id in exif:
                                date_str = exif[tag_id]
                                try:
                                    return datetime.datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                                except ValueError:
                                    pass
            except Exception:
                pass
        return datetime.datetime.fromtimestamp(os.path.getmtime(file_path))

