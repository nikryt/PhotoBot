import logging
import shutil
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import xml.etree.ElementTree as ET
from pathlib import Path
import logging
from typing import Optional



def process_single_xmp(initials: str, contacts: str, input_file: Path) -> Optional[Path]:
    """
    Обрабатывает XMP-файл:
    1. Добавляет/обновляет OrganisationInImageName
    2. Добавляет 0x8011 в FieldsToApply если отсутствует
    3. Сохраняет файл с новым именем
    """
    namespaces = {
        'x': 'adobe:ns:meta/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'photomechanic': 'http://ns.camerabits.com/photomechanic/1.0/',
        'Iptc4xmpExt': 'http://iptc.org/std/Iptc4xmpExt/2008-02-29/'
    }

    try:
        # Регистрация пространств имен
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        tree = ET.parse(input_file)
        root = tree.getroot()
        fields_to_apply = None

        # Находим необходимые элементы
        for elem in root.iter():
            if 'FieldsToApply' in elem.tag:
                fields_to_apply = elem
                break

        # Добавляем 0x8011 если отсутствует
        if fields_to_apply is not None:
            bag = fields_to_apply.find('rdf:Bag', namespaces)
            if bag is None:
                bag = ET.SubElement(fields_to_apply, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')

            hex_values = {li.text for li in bag.findall('rdf:li', namespaces)}
            if '0x8011' not in hex_values:
                new_li = ET.SubElement(bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                new_li.text = '0x8011'

        # Обновляем OrganisationInImageName (предыдущая логика)
        description = root.find('.//rdf:Description', namespaces)
        if description is None:
            raise ValueError("Не найден тег Description")

        org_name = description.find('Iptc4xmpExt:OrganisationInImageName', namespaces)
        if org_name is None:
            org_name = ET.SubElement(
                description,
                '{http://iptc.org/std/Iptc4xmpExt/2008-02-29/}OrganisationInImageName'
            )

        if (old_bag := org_name.find('rdf:Bag', namespaces)) is not None:
            org_name.remove(old_bag)

        new_bag = ET.SubElement(org_name, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')
        new_li = ET.SubElement(new_bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
        new_li.text = f"{initials} {contacts}"

        # Сохранение файла
        output_file = input_file.with_name(f"{input_file.stem}_{initials}{input_file.suffix}")
        tree.write(
            output_file,
            encoding='utf-8',
            xml_declaration=True,
            short_empty_elements=False
        )
        return output_file

    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        return None


def create_snap_file(initials: str, input_xmp: Path) -> Optional[Path]:
    """
    Преобразует XMP-файл в формат .snap, добавляя недостающие данные.

    Args:
        initials: Инициалы для формирования имени выходного файла.
        input_xmp: Путь к входному XMP-файлу.

    Returns:
        Path: Путь к созданному .snap файлу или None в случае ошибки.
    """
    namespaces = {
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
        'xmp': 'http://ns.adobe.com/xap/1.0/',
        'photomechanic': 'http://ns.camerabits.com/photomechanic/1.0/',
        'Iptc4xmpExt': 'http://iptc.org/std/Iptc4xmpExt/2008-02-29/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xmpRights': 'http://ns.adobe.com/xap/1.0/rights/'
    }

    try:
        # Регистрация пространств имен
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        # Загрузка и модификация XMP
        tree = ET.parse(input_xmp)
        root = tree.getroot()

        # Находим элемент rdf:Description
        description = root.find('.//rdf:Description', {'rdf': namespaces['rdf']})
        if not description:
            raise ValueError("Элемент rdf:Description не найден")

        # Добавляем недостающие атрибуты
        description.set(f'{{{namespaces["photoshop"]}}}DateCreated', '2025-03-29T00:00:00+05:00')
        description.set(f'{{{namespaces["xmp"]}}}CreateDate', '2025-03-29T00:00:00+05:00')
        description.set(f'{{{namespaces["xmp"]}}}Rating', '0')
        description.set(f'{{{namespaces["photomechanic"]}}}ColorClass', '0')
        description.set(f'{{{namespaces["photomechanic"]}}}Tagged', 'True')
        description.set(f'{{{namespaces["photomechanic"]}}}PMVersion', 'PM6')

        # Сериализация XMP
        xml_str = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        if xml_str.startswith('<?xml'):
            xml_str = xml_str.split('?>', 1)[-1].strip()  # Удаляем XML-декларацию

        # Создаем структуру IPTCSettings
        iptc_settings = ET.Element('IPTCSettings')
        xmp_record = ET.SubElement(iptc_settings, 'XMPRecord')
        xmp_record.text = xml_str  # Вставляем экранированный XMP

        # Добавляем фиксированные элементы
        ET.SubElement(iptc_settings, 'ApplyFlags').text =\
            '00111111110110011011010101000000000000000011000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        ET.SubElement(iptc_settings, 'MergeFlags').text =\
            '00000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'


        ET.SubElement(iptc_settings, 'ApplyDateStyle').text = '1'

        # Сохранение в файл
        output_file = input_xmp.with_name(f"IPTC_{initials}.snap")
        ET.ElementTree(iptc_settings).write(
            output_file,
            encoding='utf-8',
            xml_declaration=True
        )
        return output_file

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None


def create_ingest_snap(
        initials: str,
        raw_path: str,
        folder_format: str,
        input_ingest: Path,
        snap_content: str
) -> Optional[Path]:
    """Создает модифицированный Ingest.snap файл"""
    try:
        # Создаем новый файл вместо копирования
        output_file = input_ingest.with_name(f"Ingest_{initials}.snap")

        # Парсинг исходного файла
        tree = ET.parse(input_ingest)
        root = tree.getroot()

        # Обновление SerializedState
        if (serialized := root.find('SerializedState')) is not None:
            parts = serialized.text.split('\t')
            for i in range(len(parts)):
                if parts[i] == 'IngestPrimaryDestPath':
                    parts[i + 1] = raw_path
                elif parts[i] == 'IngestDestFolderNameString':
                    parts[i + 1] = folder_format
            serialized.text = '\t'.join(parts)

        # Обновление IPTC данных
        if (iptc := root.find('IPTCStationeryPadData')) is not None:
            # Получаем сырой XML без дополнительного экранирования
            iptc.text = snap_content.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")

        # Сохранение с правильным экранированием
        tree.write(
            output_file,
            encoding='utf-8',
            xml_declaration=True,
            short_empty_elements=False,
            method='xml'
        )

        # Ручное исправление двойного экранирования
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace("&amp;amp;", "&amp;")
        content = content.replace("&amp;lt;", "&lt;")
        content = content.replace("&amp;gt;", "&gt;")

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_file

    except Exception as e:
        logger.error(f"Ошибка создания Ingest.snap: {str(e)}")
        return None


# if __name__ == "__main__":
#     # Тестовый пример
#     try:
#         test_file = Path('PhotoMechanic' ) / 'PM_Metadata_test2.XMP'
#         result_file = process_single_xmp(
#             initials="TEST",
#             contacts="test@example.com",
#             input_file=str(test_file)
#         )
#         print(f"Тест успешен. Результат: {result_file}")
#     except Exception as e:
#         logger.error(f"Тест не пройден: {e}")