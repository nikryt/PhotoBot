import logging
import xml.etree.ElementTree as ET
import os
from pathlib import Path
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_single_xmp(initials: str, contacts: str, input_file: Path) -> Optional[Path]:
    """
    Обрабатывает XMP-файл, сохраняя оригинальную структуру и формат:
    1. Находит или создает тег OrganisationInImageName
    2. Полностью заменяет содержимое rdf:Bag
    3. Сохраняет в формате аналогичном PhotoMechanic
    """
    # Пространства имен как в оригинальном файле
    namespaces = {
        'x': 'adobe:ns:meta/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'photoshop': 'http://ns.adobe.com/photoshop/1.0/',
        'xmpRights': 'http://ns.adobe.com/xap/1.0/rights/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'photomechanic': 'http://ns.camerabits.com/photomechanic/1.0/',
        'Iptc4xmpCore': 'http://iptc.org/std/Iptc4xmpCore/1.0/xmlns/',
        'Iptc4xmpExt': 'http://iptc.org/std/Iptc4xmpExt/2008-02-29/'
    }

    try:
        # Регистрация пространств имен для сохранения оригинального формата
        for prefix, uri in namespaces.items():
            ET.register_namespace(prefix, uri)

        tree = ET.parse(input_file)
        root = tree.getroot()

        # Поиск основного тега Description
        description = root.find('.//rdf:Description', namespaces)
        if description is None:
            raise ValueError("Основной тег Description не найден")

        # Поиск или создание OrganisationInImageName
        org_name = description.find('Iptc4xmpExt:OrganisationInImageName', namespaces)
        if org_name is None:
            org_name = ET.SubElement(
                description,
                '{http://iptc.org/std/Iptc4xmpExt/2008-02-29/}OrganisationInImageName'
            )

        # Удаление старого rdf:Bag и создание нового
        if (old_bag := org_name.find('rdf:Bag', namespaces)) is not None:
            org_name.remove(old_bag)

        new_bag = ET.SubElement(org_name, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')
        new_li = ET.SubElement(new_bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
        new_li.text = f"{initials} {contacts}"

        # Сохранение файла с оригинальным форматированием
        output_file = input_file.with_name(f"{input_file.stem}_{initials}{input_file.suffix}")

        tree.write(
            output_file,
            encoding='utf-8',
            xml_declaration=True,
            short_empty_elements=False,
            method='xml'
        )

        logger.info(f"Файл успешно сохранен: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Ошибка обработки файла: {e}")
        return None


if __name__ == "__main__":
    # Тестовый пример
    try:
        test_file = Path('PhotoMechanic' ) / 'PM_Metadata_test2.XMP'
        result_file = process_single_xmp(
            initials="TEST",
            contacts="test@example.com",
            input_file=str(test_file)
        )
        print(f"Тест успешен. Результат: {result_file}")
    except Exception as e:
        logger.error(f"Тест не пройден: {e}")