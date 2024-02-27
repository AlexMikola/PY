# Цикл по всем файлам и папкам по указанному пути! Получаем лист с путями к tab файлам в папке
def getAllFileInFolder(folder):
    import os
    directory = folder
    path_tab = []
    for root, directories, filenames in os.walk(directory):
        for directory in directories:
            print(os.path.join(root, directory))
        for filename in filenames:
            if (str(filename)).lower().endswith('.tab'):
                path_tab.append(os.path.join(root, filename))
    return path_tab

# создаем (подготавливаем) каталог для файлов geojson
def createNewFolder(folder):
    import os
    path_geojson = (folder + r'\geojson')
    # проверяем, есть ли в каталоге указанная папка, если нет то создаём
    if not os.path.exists(path_geojson):
        os.mkdir(path_geojson)
        print("Directory ", path_geojson, " Created ")
    else:
        print("Directory ", path_geojson, " already exists")
    return path_geojson

#  Конвертация из плансхема метры в EPSG:4326  (WGS84) Перепроецирование
def openMiFileAndReprojection(file_tab, path_to_json):
    import geopandas as gp
    import os
    # ВАЖНЫЙ КУСОК КОДА !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    from shapely import speedups
    speedups.disable()
    # ВАЖНЫЙ КУСОК КОДА !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

    # путь к tab файлу
    daShfile = file_tab
    test = gp.read_file(daShfile)  # загрузили tab по пути в GeoDataFrame

    # готовим путь сохранения json файла
    f_name, f_ext = os.path.splitext(os.path.basename(file_tab))
    path_for_json_file = (path_to_json + '\\' + f_name + '.geojson')

    #  Конвертация
    sourceProjection = "+proj=tmerc +lat_0=55.66666666667 +lon_0=37.5 +k=1 +x_0=12 +y_0=14 +ellps=bessel +towgs84=316.151,78.924,589.65,-1.57273,2.69209,2.34693,8.4507 +units=m +no_defs"
    test.crs = sourceProjection  # Устанавливаем проекцию план схема метры текущему геодатфрэйму
    vot = test.to_crs("EPSG:4326")  # Конвертируем!!!! Перепроецируем !!!!
    vot.to_file(path_for_json_file, driver="GeoJSON")   # сохраняем результат как geojson файл

# транслитерация из кирилицы в латиницу переименовать файлы в папке (заменить русские символы на латинские)
def translitezator(folder):
    import os
    # получаем list имен файлов в каталоге
    path = folder
    r = os.listdir(path)

    # символы замен - что на что меняем
    legend = {
        ' ': '_',
        ',': '',
        'а': 'a',
        'б': 'b',
        'в': 'v',
        'г': 'g',
        'д': 'd',
        'е': 'e',
        'ё': 'yo',
        'ж': 'zh',
        'з': 'z',
        'и': 'i',
        'й': 'y',
        'к': 'k',
        'л': 'l',
        'м': 'm',
        'н': 'n',
        'о': 'o',
        'п': 'p',
        'р': 'r',
        'с': 's',
        'т': 't',
        'у': 'u',
        'ф': 'f',
        'х': 'h',
        'ц': 'c',
        'ч': 'ch',
        'ш': 'sh',
        'щ': 'shch',
        'ъ': '',
        'ы': 'y',
        'ь': '',
        'э': 'e',
        'ю': 'yu',
        'я': 'ya',
        'А': 'A',
        'Б': 'B',
        'В': 'V',
        'Г': 'G',
        'Д': 'D',
        'Е': 'E',
        'Ё': 'Yo',
        'Ж': 'Zh',
        'З': 'Z',
        'И': 'I',
        'Й': 'Y',
        'К': 'K',
        'Л': 'L',
        'М': 'M',
        'Н': 'N',
        'О': 'O',
        'П': 'P',
        'Р': 'R',
        'С': 'S',
        'Т': 'T',
        'У': 'U',
        'Ф': 'F',
        'Х': 'H',
        'Ц': 'Ts',
        'Ч': 'Ch',
        'Ш': 'Sh',
        'Щ': 'Shch',
        'Ъ': '',
        'Ы': 'Y',
        'Ь': '',
        'Э': 'E',
        'Ю': 'Yu',
        'Я': 'Ya',
    }

    # цикл по каждому имени файла
    for file_old in r:
        # до начала замены символов загоняем старое имя в новое (чтоб потом проверить изменения)
        file_new = file_old
        for i, j in legend.items():
            file_new = file_new.replace(i, j)
        if file_old != file_new:
            print('{0: <30}'.format(file_old), 'переименован в ', file_new)
            os.rename((path + "\\" + file_old), (path + "\\" + file_new))

# главная функция
def main_function(path):
    # получаем список всех .tab файлов в каталоге
    mm = getAllFileInFolder(path)

    # создаем json папку в том же каталоге где файлы tab лежат, получаем на неё ссылку
    path_to_folder_json_files = createNewFolder(path)

    # цикл по всем Mapinfo файлам с перепроецированием и сохранением в geojson файлах по созданному ранее пути
    for i in mm:
        openMiFileAndReprojection(i, path_to_folder_json_files)

    # Переименовываем по пути
    tt = translitezator(path_to_folder_json_files)

if __name__ == '__main__':
    #  !!!!!!!!!  МЕНЯЕМ ПУТЬ К TAB ФАЙЛАМ И ЗАПУСКАЕМ НА ВЫПОЛНЕНИЕ
    path_to_folder = r'C:\!_Python\!!!!_CUR'
    main_function(path_to_folder)
    print('mmm')

