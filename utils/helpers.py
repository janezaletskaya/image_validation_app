import re
from urllib.parse import urlparse, parse_qs


def extract_folder_name_from_url(url):
    """Извлекает название папки из URL Google Drive"""

    if not url:
        return ""

    try:
        # Паттерны для извлечения названий папок
        patterns = [
            r'/folders/[^/]+/([^/?&]+)',  # После ID папки
            r'folders/([^/]+)/?$',  # Название в конце URL
            r'/([^/]+)/?$'  # Последний сегмент пути
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                folder_name = match.group(1)
                # Декодируем URL-кодированные символы
                folder_name = folder_name.replace('%20', ' ')
                return folder_name

    except Exception:
        pass

    return ""


def extract_folder_id_from_url(url):
    """Извлекает ID папки из URL Google Drive"""

    if not url:
        return None

    # Паттерны для разных форматов ссылок Google Drive
    patterns = [
        r'/folders/([a-zA-Z0-9-_]+)',  # Стандартный формат
        r'id=([a-zA-Z0-9-_]+)',  # Параметр в URL
        r'/drive/folders/([a-zA-Z0-9-_]+)',  # Альтернативный формат
        r'folders/([a-zA-Z0-9-_]+)'  # Без слеша в начале
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def validate_image_filename(filename):
    """Проверяет, является ли файл изображением"""

    if not filename:
        return False

    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp',
        '.webp', '.tiff', '.tif', '.svg'
    }

    return any(filename.lower().endswith(ext) for ext in image_extensions)


def clean_filename(filename):
    """Очищает название файла от лишних символов"""

    if not filename:
        return ""

    # Удаляем ведущие и конечные пробелы
    filename = filename.strip()

    # Убираем недопустимые символы для файловой системы
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')

    return filename


def format_file_size(size_bytes):
    """Форматирует размер файла в человекочитаемый вид"""

    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1

    return f"{size_bytes:.1f} {size_names[i]}"


def validate_google_drive_url(url):
    """Валидирует URL Google Drive"""

    if not url:
        return False, "URL не может быть пустым"

    # Проверяем домен
    if 'drive.google.com' not in url:
        return False, "URL должен быть с drive.google.com"

    # Проверяем наличие folders
    if '/folders/' not in url:
        return False, "URL должен содержать '/folders/'"

    # Проверяем ID папки
    folder_id = extract_folder_id_from_url(url)
    if not folder_id:
        return False, "Не удалось извлечь ID папки"

    # Проверяем длину ID (обычно 28-44 символа)
    if len(folder_id) < 20:
        return False, "ID папки слишком короткий"

    return True, "URL валиден"


def create_direct_image_url(file_id):
    """Создает прямую ссылку на просмотр изображения"""

    if not file_id:
        return None

    return f"https://drive.google.com/file/d/{file_id}/preview"


def parse_file_list(text):
    """Парсит текст со списком файлов"""

    if not text:
        return []

    # Разбиваем по строкам
    lines = text.strip().split('\n')

    files = []
    for line in lines:
        # Очищаем строку
        filename = line.strip()

        # Пропускаем пустые строки
        if not filename:
            continue

        # Очищаем от лишних символов
        filename = clean_filename(filename)

        # Проверяем, что это файл изображения
        if validate_image_filename(filename):
            files.append(filename)

    return files


def get_category_color(category):
    """Возвращает цвет для категории одежды"""

    colors = {
        'верх': '#FF6B6B',  # Красный
        'низ': '#4ECDC4',  # Бирюзовый
        'обувь': '#45B7D1',  # Синий
        'голова': '#96CEB4',  # Зеленый
        'аксессуар': '#FFEAA7'  # Желтый
    }

    return colors.get(category, '#BDC3C7')  # Серый по умолчанию


def get_gender_emoji(gender):
    """Возвращает эмодзи для пола"""

    if gender == 'М':
        return '👨'
    elif gender == 'Ж':
        return '👩'
    elif gender == 'М/Ж':
        return '👫'
    else:
        return '❓'


def format_annotation_summary(annotation):
    """Форматирует краткое описание разметки"""

    validity_emoji = '✅' if annotation['validity'] == 'Валидно' else '❌'
    gender_emoji = get_gender_emoji(annotation['gender'])

    return f"{validity_emoji} {gender_emoji} {annotation['category']}"


def generate_filename_suggestions(folder_name, count=10):
    """Генерирует предложения названий файлов"""

    suggestions = []

    # Базовые паттерны
    base_patterns = [
        f"{folder_name}_",
        "img_",
        "photo_",
        "image_",
        ""
    ]

    # Расширения
    extensions = ['.jpg', '.jpeg', '.png']

    for i in range(1, count + 1):
        for pattern in base_patterns:
            for ext in extensions:
                suggestions.append(f"{pattern}{i:03d}{ext}")

    return suggestions[:count]


def sanitize_folder_name(name):
    """Очищает название папки для использования в путях"""

    if not name:
        return "unknown"

    # Приводим к нижнему регистру
    name = name.lower().strip()

    # Заменяем пробелы на подчеркивания
    name = re.sub(r'\s+', '_', name)

    # Убираем недопустимые символы
    name = re.sub(r'[^\w\-_]', '', name)

    # Убираем множественные подчеркивания
    name = re.sub(r'_+', '_', name)

    # Убираем подчеркивания в начале и конце
    name = name.strip('_')

    return name or "unknown"


def validate_annotation_data(data):
    """Валидирует данные разметки"""

    errors = []

    # Проверяем обязательные поля
    required_fields = ['validity', 'gender', 'category']

    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Поле '{field}' обязательно")

    # Проверяем валидность значений
    if 'validity' in data:
        if data['validity'] not in ['Валидно', 'Невалидно']:
            errors.append("Валидность должна быть 'Валидно' или 'Невалидно'")

    if 'gender' in data:
        valid_genders = ['М', 'Ж', 'М/Ж']
        if data['gender'] not in valid_genders:
            errors.append(f"Пол должен быть одним из: {valid_genders}")

    if 'category' in data:
        valid_categories = ['верх', 'низ', 'обувь', 'голова', 'аксессуар']
        if data['category'] not in valid_categories:
            errors.append(f"Категория должна быть одной из: {valid_categories}")

    return len(errors) == 0, errors