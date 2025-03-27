import xml.etree.ElementTree as ET
import os


def process_single_xmp(initials: str, contacts: str, input_file: str) -> str:
    """
    Обрабатывает XMP-файл:
    - Если тег OrganisationInImageName отсутствует, создает его.
    - Вставляет инициалы и контакты в тег.
    - Сохраняет файл с новым именем (с суффиксом инициалов).
    """
    namespaces = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'Iptc4xmpExt': 'http://iptc.org/std/Iptc4xmpExt/2008-02-29/',
        'x': 'adobe:ns:meta/'
    }

    try:
        # Загрузка и парсинг XML
        tree = ET.parse(input_file)
        root = tree.getroot()

        # Находим корневой элемент Description
        description = root.find('.//rdf:Description', namespaces)
        if description is None:
            raise ValueError("Не найден тег rdf:Description.")

        # Поиск тега OrganisationInImageName
        org_name = description.find('Iptc4xmpExt:OrganisationInImageName', namespaces)

        # Если тег отсутствует, создаем его
        if org_name is None:
            org_name = ET.SubElement(
                description,
                '{http://iptc.org/std/Iptc4xmpExt/2008-02-29/}OrganisationInImageName'
            )
            rdf_bag = ET.SubElement(org_name, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')
        else:
            # Иначе ищем существующий rdf:Bag
            rdf_bag = org_name.find('rdf:Bag', namespaces)
            if rdf_bag is None:
                rdf_bag = ET.SubElement(org_name, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')

        # Очищаем старые данные (если есть) и добавляем новые
        rdf_bag.clear()
        new_li = ET.SubElement(rdf_bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
        new_li.text = f"{initials} {contacts}"

        # Сохраняем файл
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_{initials}.txt"
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        return output_file

    except ET.ParseError as e:
        raise ValueError(f"Ошибка парсинга XML: {e}")
    except Exception as e:
        raise RuntimeError(f"Ошибка обработки файла: {e}")

try:
    new_file = process_single_xmp(
        initials="KNA",
        contacts="@nikryt",
        input_file=('PM_Metadata_test2.XMP')

    )
    print(f"Файл успешно обработан и сохранен как: {new_file}")
except Exception as e:
    print(f"Ошибка: {e}")