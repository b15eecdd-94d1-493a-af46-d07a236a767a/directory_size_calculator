import os
import time
import math
import traceback
import pathlib

def human_readable_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

class DirectorySizeCalculator:
    def __init__(self):
        self.directory_sizes = {}
        self.directory_sizes_detail = {}
        self.errors = []

    def scandir(self, directory):
        try:
            return os.scandir(directory)
        except Exception as error:
            if len(self.errors) == 0:
                file_mode = 'w'
            else:
                file_mode = 'a'
            self.errors.append(traceback.format_exc())  
            with open("exceptions.log", file_mode) as logfile:
                traceback.print_exc(file=logfile)
            return []

    def add_detail(self, directory, filepath, filesize = False):
        if filesize == False:
            filesize = os.path.getsize(filepath)
        file_suffix = pathlib.Path(filepath).suffix.lower()
        if directory not in self.directory_sizes_detail:
            self.directory_sizes_detail[directory] = {}
        if 'type' not in self.directory_sizes_detail[directory]:
            self.directory_sizes_detail[directory]['type'] = {'video': 0, 'audio': 0, 'doc': 0, 'sub': 0, 'image': 0, 'archive': 0, 'over': 0} 
        if 'ext' not in self.directory_sizes_detail[directory]:
            self.directory_sizes_detail[directory]['ext'] = {}
        if file_suffix not in self.directory_sizes_detail[directory]['ext']:
            self.directory_sizes_detail[directory]['ext'][file_suffix] = 0
        self.directory_sizes_detail[directory]['ext'][file_suffix] += filesize
        if file_suffix in ['.mp4', '.webm', '.avi', '.mkv', '.mov', '.ogg', '.wmv']:
            self.directory_sizes_detail[directory]['type']['video'] += filesize
        elif file_suffix in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
            self.directory_sizes_detail[directory]['type']['image'] += filesize
        elif file_suffix in ['.txt', '.odt', '.ods', '.odp', '.php', '.cpp', '.py', '.pl', '.html', '.js', '.css', '.pdf', '.go' , '.mhtml', '.xml', '.json', '.docx']:
            self.directory_sizes_detail[directory]['type']['doc'] += filesize
        elif file_suffix in ['.mp3', '.flac', '.m4a']:
            self.directory_sizes_detail[directory]['type']['audio'] += filesize
        elif file_suffix in ['.srt', '.ass', '.vtt']:
            self.directory_sizes_detail[directory]['type']['sub'] += filesize
        elif file_suffix in ['.zip', '.rar', '.gzip', '.gz', '.tar']:
            self.directory_sizes_detail[directory]['type']['archive'] += filesize
        else:
            self.directory_sizes_detail[directory]['type']['over'] += filesize

    def size_files_in_directory(self, directory, max_depth = 10, current_depth = 0):
        dir_size = 0
        if current_depth < max_depth:
            self.directory_sizes[directory] = (0, current_depth)
        for entry in self.scandir(directory):
            if entry.is_file():
                filesize = os.path.getsize(entry)
                dir_size += filesize
                self.add_detail(directory, entry.path, filesize)
            elif entry.is_dir():
                subdir_size = self.size_files_in_directory(entry.path, max_depth, current_depth + 1)
                if current_depth < max_depth:
                    self.directory_sizes[entry.path] = subdir_size
                dir_size += subdir_size[0]
                if entry.path in self.directory_sizes_detail:
                    if directory not in self.directory_sizes_detail:
                        self.directory_sizes_detail[directory] = {}
                        self.directory_sizes_detail[directory]['type'] = {}
                        self.directory_sizes_detail[directory]['ext'] = {}
                    for entry_size_detail_type, entry_size_detail_value in self.directory_sizes_detail[entry.path]['type'].items():
                        if entry_size_detail_type not in self.directory_sizes_detail[directory]['type']:
                            self.directory_sizes_detail[directory]['type'][entry_size_detail_type] = 0
                        self.directory_sizes_detail[directory]['type'][entry_size_detail_type] += entry_size_detail_value
                    for entry_size_detail_ext, entry_size_detail_value in self.directory_sizes_detail[entry.path]['ext'].items():
                        if entry_size_detail_ext not in self.directory_sizes_detail[directory]['ext']:
                            self.directory_sizes_detail[directory]['ext'][entry_size_detail_ext] = 0
                        self.directory_sizes_detail[directory]['ext'][entry_size_detail_ext] += entry_size_detail_value
        if current_depth < max_depth:
            self.directory_sizes[directory] = (dir_size, current_depth)
        return (dir_size, current_depth)
    
    def _size_files_in_directory(self, directory):
        dir_size = 0
        for entry in self.scandir(directory):
            if entry.is_file():
                dir_size += os.path.getsize(entry)
            elif entry.is_dir():
                dir_size += self._size_files_in_directory(entry.path)
        return dir_size
    
    def get_errors(self):
        return self.errors
    
    def print_errors(self):
        for error in self.errors:
            print(error)

# Использование класса
if __name__ == "__main__":
    size_canculator = DirectorySizeCalculator()
    input_directory_path = input('Путь к каталогу: ').strip()  # Укажите путь к вашему каталогу
    input_max_depth = input('Максимальная вложенность: ')
    if input_directory_path.endswith('/'):
        input_directory_path = input_directory_path[:-1]
    size_canculator.size_files_in_directory(input_directory_path, int(input_max_depth))
    i = 0
    for dir_info in size_canculator.directory_sizes.items():
        dir_path = os.path.basename(dir_info[0])
        dir_size = human_readable_size(dir_info[1][0])
        if i == 0:
            print('')
        if dir_info[1][1] == 1 and i != 0:
            print('')
        prefix = '-' * dir_info[1][1]
        if prefix != '':
            prefix += ' '
        print(f"{prefix}{dir_path} | {dir_size}", end="") 
        if dir_info[0] in size_canculator.directory_sizes_detail:
            i_file_type_size = 0
            print_file_type_size = []
            for file_type, file_type_size in size_canculator.directory_sizes_detail[dir_info[0]]['type'].items():
                if i_file_type_size == 0:
                    print(' [ ', end='')
                if file_type_size > 0:
                    print_file_type_size.append(file_type + ':' + str(human_readable_size(file_type_size)),)
                i_file_type_size += 1
            """
            for file_type, file_type_size in size_canculator.directory_sizes_detail[dir_info[0]]['ext'].items():
                if i_file_type_size == 0:
                    print(' | ', end='')
                if file_type_size > 0:
                    print_file_type_size.append(file_type + ':' + str(human_readable_size(file_type_size)),)
                i_file_type_size += 1
            """
            if i_file_type_size > 0:
                print(', '.join(print_file_type_size), end="")
        print(' ]')
        i += 1
    if len(size_canculator.get_errors()) > 0:
        print('\nОбнаружены ошибки, посмотрите файл exceptions.log')
    #size_canculator.print_errors()
