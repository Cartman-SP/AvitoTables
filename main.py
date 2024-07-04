import gspread
from oauth2client.service_account import ServiceAccountCredentials
import xml.etree.ElementTree as ET
from avitoapi import get_balance,get_avance, get_avito_ids
from gspread.cell import Cell
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Загружаем учетные данные из JSON-файла
creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', scope)

# Авторизуемся
client = gspread.authorize(creds)

spreadsheet_url = "https://docs.google.com/spreadsheets/d/10GdbmK80sJFRWtyFlBYxH4fTRsHry1Tihc9NR6Ybdm0/edit?gid=1540310819#gid=1540310819"
spreadsheet = client.open_by_url(spreadsheet_url)

# Получаем все листы документа
worksheets = spreadsheet.worksheets()

# Функция для добавления отступов
def indent(elem, level=0):
    i = "\n" + level * "    "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "    "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


# Проходимся по всем листам
for worksheet in worksheets[2:]:
    
    data = worksheet.get_all_values()

    client_id = data[0][0]
    client_secret =data[0][1]
    balance = get_balance(client_id,client_secret)
    worksheet.update_cell(1, 8, str(balance['real']))
    avance = get_avance(client_id,client_secret)
    worksheet.update_cell(1, 10, str(avance))
    headers = data[1][:-3]
    # Создаем корневой элемент XML-документа
    root = ET.Element("Ads", formatVersion="3", target="Avito.ru")
    row_id = 3
    cells = {'items':[]}
    for row in data[2:]:
        if all(cell == '' for cell in row):
            break
        print(row[0])
        if(not(row[0])):
            continue
        item = ET.Element("Ad")
        # Добавляем элементы для каждого поля строки
        cells['items'].append({'row':row_id,'id':row[0]})
        for header, value in zip(headers, row):
            if header == "ImageUrls":
                images_element = ET.SubElement(item, "Images")
                image_urls = value.split(",")  # Разделяем URL-ы, если они разделены запятыми
                for url in image_urls:
                    image_element = ET.SubElement(images_element, "Image")
                    image_element.set("url", url)
            elif header == "SalaryRange":
                # Разделяем значение на части "от" и "до"
                from_salary, to_salary = value.split("|")
                
                # Создаем элементы XML для SalaryRange
                salary_range_element = ET.SubElement(item, "SalaryRange")
                from_element = ET.SubElement(salary_range_element, "From")
                from_element.text = from_salary
                to_element = ET.SubElement(salary_range_element, "To")
                to_element.text = to_salary
            else:
                # Создаем обычный элемент XML для других заголовков
                child = ET.SubElement(item, header)
                child.text = value
        root.append(item)
        row_id+=1
    statistic = get_avito_ids(client_id,client_secret,cells)
    cell_updates = []
    for i in statistic:
        cell_updates.append(Cell(i['row'], 23, i['uniqViews']))
        cell_updates.append(Cell(i['row'], 24, i['uniqContacts']))
        cell_updates.append(Cell(i['row'], 25, i['status']))
    # Добавляем отступы
    worksheet.update_cells(cell_updates)
    indent(root)

    # Создаем объект дерева XML
    tree = ET.ElementTree(root)

    # Формируем имя файла
    file_name = f"data{worksheet.id}.xml"

    # Записываем дерево в XML-файл без декларации
    with open(f"{file_name}", "wb") as f:
        tree.write(f, encoding='utf-8', xml_declaration=False)

    # Записываем ссылку на скачивание файла в первую строку первой колонки
    download_url = f"http://158.255.5.151:5000/download/{file_name}"
    worksheet.update_cell(1, 3, download_url)
