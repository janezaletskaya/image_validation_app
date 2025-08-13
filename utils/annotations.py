import streamlit as st
import pandas as pd


def save_annotation(filename, validity, gender, category, folder_name, notes=""):
    """Сохраняет разметку изображения"""

    try:
        annotation = {
            'img_path': f"{folder_name}/{filename}",
            'filename': filename,
            'validity': validity,
            'gender': gender,
            'category': category,
            'folder': folder_name,
            'notes': notes
        }

        # Проверяем, есть ли уже разметка для этого изображения
        existing_index = None
        for i, ann in enumerate(st.session_state.annotations):
            if ann['filename'] == filename:
                existing_index = i
                break

        if existing_index is not None:
            # Обновляем существующую разметку
            st.session_state.annotations[existing_index] = annotation
        else:
            # Добавляем новую разметку
            st.session_state.annotations.append(annotation)

        return True

    except Exception as e:
        st.error(f"Ошибка при сохранении разметки: {str(e)}")
        return False


def get_current_annotation(filename):
    """Получает текущую разметку для изображения"""

    for ann in st.session_state.annotations:
        if ann['filename'] == filename:
            return ann
    return None


def delete_annotation(filename):
    """Удаляет разметку для изображения"""

    st.session_state.annotations = [
        ann for ann in st.session_state.annotations
        if ann['filename'] != filename
    ]


def export_to_csv(annotations):
    """Экспортирует разметки в CSV формат"""

    if not annotations:
        return None

    # Создаем DataFrame с нужными колонками
    df = pd.DataFrame(annotations)

    # Выбираем нужные колонки в правильном порядке
    export_columns = ['img_path', 'validity', 'gender', 'category']

    # Проверяем наличие колонок
    missing_columns = [col for col in export_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Отсутствуют колонки: {missing_columns}")
        return None

    csv_data = df[export_columns].copy()
    return csv_data.to_csv(index=False)


def get_annotation_stats():
    """Возвращает статистику разметок"""

    if not st.session_state.annotations:
        return {
            'total': 0,
            'valid': 0,
            'invalid': 0,
            'by_gender': {},
            'by_category': {}
        }

    df = pd.DataFrame(st.session_state.annotations)

    # Базовая статистика
    total = len(df)
    valid_count = len(df[df['validity'] == 'Валидно'])
    invalid_count = len(df[df['validity'] == 'Невалидно'])

    # Статистика по полу
    gender_stats = {}
    for gender in ['М', 'Ж', 'М/Ж']:
        count = len(df[df['gender'] == gender])
        if count > 0:
            gender_stats[gender] = count

    # Статистика по категориям
    category_stats = df['category'].value_counts().to_dict()

    return {
        'total': total,
        'valid': valid_count,
        'invalid': invalid_count,
        'by_gender': gender_stats,
        'by_category': category_stats
    }


def validate_annotation(annotation):
    """Валидирует разметку перед сохранением"""

    required_fields = ['filename', 'validity', 'gender', 'category']

    for field in required_fields:
        if field not in annotation or not annotation[field]:
            return False, f"Поле '{field}' обязательно для заполнения"

    # Проверяем валидные значения
    if annotation['validity'] not in ['Валидно', 'Невалидно']:
        return False, "Неверное значение валидности"

    valid_categories = ['верх', 'низ', 'обувь', 'голова', 'аксессуар']
    if annotation['category'] not in valid_categories:
        return False, "Неверная категория"

    # Проверяем формат пола
    valid_genders = ['М', 'Ж', 'М/Ж']
    if annotation['gender'] not in valid_genders:
        return False, "Неверный формат пола"

    return True, "OK"


def bulk_update_annotations(updates):
    """Массовое обновление разметок"""

    updated_count = 0

    for filename, annotation_data in updates.items():
        try:
            success = save_annotation(
                filename=filename,
                validity=annotation_data['validity'],
                gender=annotation_data['gender'],
                category=annotation_data['category'],
                folder_name=annotation_data.get('folder', st.session_state.folder_name),
                notes=annotation_data.get('notes', '')
            )

            if success:
                updated_count += 1

        except Exception as e:
            st.error(f"Ошибка при обновлении {filename}: {str(e)}")

    return updated_count


def clear_all_annotations():
    """Очищает все разметки"""

    st.session_state.annotations = []


def get_unannotated_files():
    """Возвращает список неразмеченных файлов"""

    if not st.session_state.images_list:
        return []

    annotated_files = {ann['filename'] for ann in st.session_state.annotations}

    return [
        filename for filename in st.session_state.images_list
        if filename not in annotated_files
    ]


def get_next_unannotated_index():
    """Возвращает индекс следующего неразмеченного файла"""

    unannotated_files = get_unannotated_files()

    if not unannotated_files:
        return None

    # Ищем первый неразмеченный файл после текущего
    current_idx = st.session_state.current_image_index

    for i in range(current_idx + 1, len(st.session_state.images_list)):
        if st.session_state.images_list[i] in unannotated_files:
            return i

    # Если не найден после текущего, ищем с начала
    for i in range(current_idx):
        if st.session_state.images_list[i] in unannotated_files:
            return i

    return None


def import_annotations_from_csv(csv_file):
    """Импортирует разметки из CSV файла"""

    try:
        df = pd.read_csv(csv_file)

        required_columns = ['img_path', 'validity', 'gender', 'category']
        if not all(col in df.columns for col in required_columns):
            return False, f"CSV должен содержать колонки: {required_columns}"

        imported_count = 0

        for _, row in df.iterrows():
            # Извлекаем filename из img_path
            img_path = row['img_path']
            filename = img_path.split('/')[-1] if '/' in img_path else img_path

            # Проверяем, есть ли такой файл в списке
            if filename in st.session_state.images_list:
                annotation = {
                    'img_path': img_path,
                    'filename': filename,
                    'validity': row['validity'],
                    'gender': row['gender'],
                    'category': row['category'],
                    'folder': st.session_state.folder_name,
                    'notes': row.get('notes', '')
                }

                # Валидируем разметку
                is_valid, message = validate_annotation(annotation)
                if is_valid:
                    # Добавляем или обновляем разметку
                    existing_index = None
                    for i, ann in enumerate(st.session_state.annotations):
                        if ann['filename'] == filename:
                            existing_index = i
                            break

                    if existing_index is not None:
                        st.session_state.annotations[existing_index] = annotation
                    else:
                        st.session_state.annotations.append(annotation)

                    imported_count += 1

        return True, f"Импортировано {imported_count} разметок"

    except Exception as e:
        return False, f"Ошибка при импорте: {str(e)}"