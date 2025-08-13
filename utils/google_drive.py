import streamlit as st
import requests
import re
from urllib.parse import urlparse, parse_qs
import json


def extract_folder_id_from_url(url):
    """Извлекает ID папки из URL Google Drive"""
    if not url:
        return None

    patterns = [
        r'/folders/([a-zA-Z0-9-_]+)',
        r'id=([a-zA-Z0-9-_]+)',
        r'/drive/folders/([a-zA-Z0-9-_]+)'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_files_from_public_folder(folder_url):
    """
    Получает список файлов из публичной папки Google Drive
    Использует веб-скрейпинг, так как папка публичная
    """

    folder_id = extract_folder_id_from_url(folder_url)
    if not folder_id:
        raise Exception("Не удалось извлечь ID папки из URL")

    try:
        # Формируем URL для получения списка файлов
        api_url = f"https://drive.google.com/drive/folders/{folder_id}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Делаем запрос
        response = requests.get(api_url, headers=headers, timeout=15)

        if response.status_code != 200:
            raise Exception(f"Ошибка доступа к папке: HTTP {response.status_code}")

        # Парсим HTML для извлечения информации о файлах
        html_content = response.text

        # Ищем JSON данные в HTML
        files_data = extract_files_from_html(html_content)

        if not files_data:
            # Альтернативный метод - через embeddedfolderview
            return get_files_alternative_method(folder_id)

        return files_data

    except requests.RequestException as e:
        raise Exception(f"Ошибка сети: {str(e)}")
    except Exception as e:
        raise Exception(f"Ошибка при получении файлов: {str(e)}")


def extract_files_from_html(html_content):
    """Извлекает информацию о файлах из HTML страницы Google Drive"""

    files = []

    # Паттерны для поиска файлов изображений
    image_patterns = [
        r'"([^"]*\.(?:jpg|jpeg|png|gif|bmp|webp))"[^"]*"([^"]*)"',
        r"'([^']*\.(?:jpg|jpeg|png|gif|bmp|webp))'[^']*'([^']*)'",
        # Поиск ID файлов и имен
        r'"id":"([^"]{20,})"[^}]*"name":"([^"]*\.(?:jpg|jpeg|png|gif|bmp|webp))"',
    ]

    for pattern in image_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE)
        for match in matches:
            if len(match) == 2:
                # Определяем, что является именем файла, а что ID
                if '.' in match[0] and len(match[1]) > 20:  # match[0] - имя, match[1] - ID
                    filename = match[0]
                    file_id = match[1]
                elif '.' in match[1] and len(match[0]) > 20:  # match[1] - имя, match[0] - ID
                    filename = match[1]
                    file_id = match[0]
                else:
                    continue

                if is_image_file(filename):
                    files.append({
                        'filename': filename,
                        'file_id': file_id,
                        'view_url': f"https://drive.google.com/file/d/{file_id}/preview"
                    })

    # Убираем дубликаты по имени файла
    seen_names = set()
    unique_files = []
    for file_info in files:
        if file_info['filename'] not in seen_names:
            seen_names.add(file_info['filename'])
            unique_files.append(file_info)

    return unique_files


def get_files_alternative_method(folder_id):
    """Альтернативный метод получения файлов через embeddedfolderview"""

    try:
        embed_url = f"https://drive.google.com/embeddedfolderview?id={folder_id}#list"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(embed_url, headers=headers, timeout=10)

        if response.status_code == 200:
            html = response.text

            # Простой поиск имен файлов изображений
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
            files = []

            for ext in image_extensions:
                pattern = rf'["\']([^"\']*\.{ext})["\']'
                matches = re.findall(pattern, html, re.IGNORECASE)

                for filename in matches:
                    if is_image_file(filename) and len(filename) > 3:
                        files.append({
                            'filename': filename,
                            'file_id': None,  # Не можем получить ID этим методом
                            'view_url': None
                        })

            # Убираем дубликаты
            seen = set()
            unique_files = []
            for file_info in files:
                if file_info['filename'] not in seen:
                    seen.add(file_info['filename'])
                    unique_files.append(file_info)

            return unique_files

    except Exception as e:
        st.error(f"Альтернативный метод не сработал: {str(e)}")

    return []


def is_image_file(filename):
    """Проверяет, является ли файл изображением"""
    if not filename:
        return False

    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    return any(filename.lower().endswith(ext) for ext in image_extensions)


def test_folder_access(folder_url):
    """Тестирует доступ к папке Google Drive"""

    folder_id = extract_folder_id_from_url(folder_url)
    if not folder_id:
        return False, "Неверный URL папки"

    try:
        test_url = f"https://drive.google.com/drive/folders/{folder_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(test_url, headers=headers, timeout=10)

        if response.status_code == 200:
            if 'This folder doesn\'t exist' in response.text:
                return False, "Папка не существует или нет доступа"
            return True, "Доступ к папке есть"
        elif response.status_code == 403:
            return False, "Нет прав доступа к папке"
        elif response.status_code == 404:
            return False, "Папка не найдена"
        else:
            return False, f"HTTP ошибка: {response.status_code}"

    except Exception as e:
        return False, f"Ошибка подключения: {str(e)}"


def get_direct_download_url(file_id):
    """Создает прямую ссылку для скачивания файла"""
    if not file_id:
        return None
    return f"https://drive.google.com/uc?export=download&id={file_id}"


def get_preview_url(file_id):
    """Создает ссылку для предварительного просмотра"""
    if not file_id:
        return None
    return f"https://drive.google.com/file/d/{file_id}/preview"


@st.cache_data(ttl=300)  # Кэшируем на 5 минут
def cached_get_files_from_folder(folder_url):
    """Кэшированная версия получения файлов"""
    return get_files_from_public_folder(folder_url)


def format_file_info(files_data):
    """Форматирует информацию о файлах для отображения"""

    if not files_data:
        return "Файлы не найдены"

    info_lines = []
    info_lines.append(f"📁 Найдено файлов: {len(files_data)}")
    info_lines.append("")

    for i, file_info in enumerate(files_data[:10], 1):  # Показываем первые 10
        filename = file_info['filename']
        status = "✅" if file_info.get('file_id') else "❓"
        info_lines.append(f"{i}. {status} {filename}")

    if len(files_data) > 10:
        info_lines.append(f"... и еще {len(files_data) - 10} файлов")

    return "\n".join(info_lines)


def validate_files_data(files_data):
    """Валидирует полученные данные о файлах"""

    if not files_data:
        return False, "Список файлов пуст"

    if not isinstance(files_data, list):
        return False, "Неверный формат данных"

    image_files = [f for f in files_data if is_image_file(f.get('filename', ''))]

    if not image_files:
        return False, "Не найдено файлов изображений"

    if len(image_files) < len(files_data) * 0.5:
        return False, "Слишком мало файлов изображений"

    return True, f"Найдено {len(image_files)} изображений"