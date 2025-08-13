import streamlit as st
import pandas as pd
import os
from PIL import Image
import tempfile
import zipfile
import gdown
import time
from components.sidebar import render_sidebar
from components.navigation import render_navigation
from components.annotation_form import render_annotation_form
from utils.annotations import export_to_csv

# Настройка страницы
st.set_page_config(
    page_title="Разметка изображений Google Drive",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация session state
if 'annotations' not in st.session_state:
    st.session_state.annotations = []
if 'current_image_index' not in st.session_state:
    st.session_state.current_image_index = 0
if 'images_list' not in st.session_state:
    st.session_state.images_list = []
if 'image_paths' not in st.session_state:
    st.session_state.image_paths = {}
if 'folder_name' not in st.session_state:
    st.session_state.folder_name = ""


@st.cache_data
def load_images_from_gdrive_zip(gdrive_url, folder_name):
    """Загружает изображения из ZIP архива на Google Drive"""
    try:
        # Создаем временную директорию
        temp_dir = tempfile.mkdtemp()

        # Извлекаем ID из ссылки Google Drive
        if 'drive.google.com' in gdrive_url:
            if '/file/d/' in gdrive_url:
                file_id = gdrive_url.split('/file/d/')[1].split('/')[0]
            elif '?id=' in gdrive_url:
                file_id = gdrive_url.split('?id=')[1].split('&')[0]
            elif '/open?id=' in gdrive_url:
                file_id = gdrive_url.split('/open?id=')[1].split('&')[0]
            else:
                st.error("Неверный формат ссылки Google Drive. Нужна ссылка на файл.")
                return None, None
        else:
            st.error("Ссылка должна быть из Google Drive")
            return None, None

        # Скачиваем ZIP файл
        zip_path = os.path.join(temp_dir, "images.zip")
        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"

        with st.spinner("Скачиваем ZIP архив..."):
            try:
                gdown.download(download_url, zip_path, quiet=False)
            except Exception as e:
                # Пробуем альтернативный метод
                st.warning("Пробуем альтернативный способ скачивания...")
                download_url = f"https://drive.google.com/uc?id={file_id}"
                gdown.download(download_url, zip_path, quiet=False)

        # Проверяем, что файл скачался
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
            st.error("Не удалось скачать файл. Проверьте ссылку и права доступа.")
            return None, None

        # Распаковываем ZIP
        extract_dir = os.path.join(temp_dir, "extracted")
        with st.spinner("Извлекаем изображения..."):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

        # Находим изображения
        images = []
        image_paths = {}

        for root, dirs, files in os.walk(extract_dir):
            # Пропускаем служебные папки
            if '__MACOSX' in root or '.DS_Store' in root:
                continue

            for file in files:
                # Пропускаем служебные файлы
                if file.startswith('._') or file.startswith('.DS_Store') or file.startswith('Thumbs.db'):
                    continue

                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')):
                    full_path = os.path.join(root, file)

                    # Проверяем, что файл можно открыть
                    try:
                        with Image.open(full_path) as test_img:
                            test_img.verify()

                        # Переоткрываем файл (verify() закрывает его)
                        with Image.open(full_path) as img:
                            # Проверяем размер изображения
                            if img.size[0] > 50 and img.size[1] > 50:  # Минимальный размер
                                images.append(file)
                                image_paths[file] = full_path
                    except Exception as e:
                        st.warning(f"Пропускаем поврежденный файл {file}: {e}")

        if not images:
            st.error("В архиве не найдено изображений")
            return None, None

        st.success(f"✅ Загружено {len(images)} изображений")
        return images, image_paths

    except Exception as e:
        st.error(f"Ошибка загрузки ZIP архива: {e}")
        return None, None


def main():
    # Заголовок приложения
    st.title("🏷️ Разметка изображений из Google Drive")
    st.markdown("*Загрузите ZIP архив с изображениями и размечайте их*")

    # Боковая панель для загрузки
    render_zip_upload_sidebar()

    # Основной контент
    if not st.session_state.images_list:
        show_welcome_screen()
    else:
        show_annotation_interface()

    # Панель экспорта
    if st.session_state.annotations:
        show_export_panel()


def render_zip_upload_sidebar():
    """Рендерит боковую панель для загрузки ZIP"""

    with st.sidebar:
        st.header("📦 Загрузка ZIP архива")

        # Инструкция
        with st.expander("📖 Как подготовить архив"):
            st.markdown("""
            **Шаги:**
            1. Создайте папку с изображениями на компьютере
            2. Заархивируйте папку в ZIP
            3. Загрузите ZIP на Google Drive
            4. Получите ссылку: "Поделиться" → "Копировать ссылку"
            5. Вставьте ссылку ниже

            **Требования:**
            - ZIP архив должен быть доступен по ссылке
            - Поддерживаемые форматы: JPG, PNG, GIF, BMP, WEBP
            """)

        # Ссылка на ZIP архив
        gdrive_url = st.text_input(
            "🔗 Ссылка на ZIP архив:",
            placeholder="https://drive.google.com/file/d/1ABC.../view?usp=sharing",
            help="Ссылка на ZIP архив в Google Drive"
        )

        # Название папки/категории
        folder_name = st.text_input(
            "📁 Категория одежды:",
            placeholder="юбка, штаны, шорты...",
            help="Название категории для разметки"
        )

        # Кнопка загрузки
        if st.button("📥 Загрузить изображения", use_container_width=True):
            if not gdrive_url:
                st.error("❌ Введите ссылку на ZIP архив")
            elif not folder_name:
                st.error("❌ Укажите категорию одежды")
            else:
                # Загружаем изображения
                images, image_paths = load_images_from_gdrive_zip(gdrive_url, folder_name)

                if images and image_paths:
                    # Сохраняем в session state
                    st.session_state.images_list = images
                    st.session_state.image_paths = image_paths
                    st.session_state.folder_name = folder_name
                    st.session_state.current_image_index = 0
                    st.session_state.gdrive_url = gdrive_url

                    st.rerun()

        # Показываем информацию о загруженных изображениях
        if st.session_state.images_list:
            st.markdown("---")
            st.subheader("📊 Информация")

            total_images = len(st.session_state.images_list)
            annotated_count = len(st.session_state.annotations)

            st.metric("Всего изображений", total_images)
            st.metric("Размечено", annotated_count)

            if total_images > 0:
                progress = annotated_count / total_images
                st.progress(progress)
                st.caption(f"{progress * 100:.1f}% завершено")

            # Действия
            st.markdown("**🔧 Действия:**")

            if st.button("🗑️ Очистить разметки", use_container_width=True):
                st.session_state.annotations = []
                st.success("Разметки очищены")
                st.rerun()

            if st.button("🔄 Загрузить новый архив", use_container_width=True):
                # Очищаем все данные
                st.session_state.images_list = []
                st.session_state.image_paths = {}
                st.session_state.annotations = []
                st.session_state.folder_name = ""
                st.session_state.current_image_index = 0
                st.rerun()


def show_welcome_screen():
    """Показывает приветственный экран"""
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.info(
            "👆 **Начните работу:**\n1. Подготовьте ZIP архив с изображениями\n2. Загрузите на Google Drive\n3. Вставьте ссылку в боковой панели")

    with col2:
        st.markdown("### 📦 Пример ZIP архива:")
        st.code("""images.zip
├── image1.jpg
├── image2.png  
├── photo3.jpeg
└── picture4.jpg""")

    # Подробная инструкция
    with st.expander("📋 Подробная инструкция"):
        st.markdown("""
        ### 🔧 Создание ZIP архива:

        1. **Создайте папку** на компьютере с изображениями одежды
        2. **Заархивируйте папку** в ZIP (правый клик → "Сжать в ZIP")
        3. **Загрузите ZIP на Google Drive**

        ### 🔗 Получение ссылки:

        1. **Откройте ZIP файл** в Google Drive
        2. **Нажмите "Поделиться"** (значок с человечками)
        3. **Измените доступ** на "Просмотр для всех, у кого есть ссылка"
        4. **Скопируйте ссылку** и вставьте в поле выше

        ### 🏷️ Разметка изображений:

        - **Валидность:** подходит ли изображение для обучения
        - **Пол:** мужская/женская одежда (можно оба)
        - **Категория:** тип одежды (верх/низ/обувь/голова/аксессуар)

        ### 📥 Экспорт результатов:

        По завершении работы скачайте CSV файл с результатами разметки.
        """)


def show_annotation_interface():
    """Показывает интерфейс разметки"""
    st.markdown("---")

    # Навигация
    render_navigation()

    st.markdown("---")

    # Основной интерфейс
    current_idx = st.session_state.current_image_index
    current_filename = st.session_state.images_list[current_idx]

    col1, col2 = st.columns([2, 1])

    with col1:
        show_image_area(current_filename)

    with col2:
        render_annotation_form(current_filename)


def show_image_area(filename):
    """Показывает область изображения"""
    st.markdown("### 🖼️ Изображение")

    # Компактная информация о файле
    st.info(f"📁 **Файл:** {filename}\n📂 **Категория:** {st.session_state.folder_name}")

    # Показываем изображение из загруженного архива
    if filename in st.session_state.image_paths:
        try:
            img_path = st.session_state.image_paths[filename]
            img = Image.open(img_path)
            st.image(img, use_container_width=True, caption=filename)

        except Exception as e:
            st.error(f"❌ Ошибка загрузки изображения: {str(e)}")
            show_placeholder_image()
    else:
        st.error("❌ Файл изображения не найден")
        show_placeholder_image()


def show_placeholder_image():
    """Показывает заглушку изображения"""
    st.image("https://via.placeholder.com/500x350/f8f9fa/6c757d?text=Изображение+не+найдено",
             use_container_width=True,
             caption="Изображение недоступно")


def show_export_panel():
    """Показывает панель экспорта результатов"""
    st.markdown("---")
    st.header("📤 Экспорт результатов")

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        annotated_count = len(st.session_state.annotations)
        total_count = len(st.session_state.images_list)
        st.metric("Прогресс разметки", f"{annotated_count}/{total_count}")

        if total_count > 0:
            progress_percent = (annotated_count / total_count) * 100
            st.progress(progress_percent / 100)
            st.caption(f"{progress_percent:.1f}% завершено")

    with col2:
        if st.button("📊 Показать таблицу", use_container_width=True):
            if st.session_state.annotations:
                df = pd.DataFrame(st.session_state.annotations)
                st.dataframe(df[['img_path', 'validity', 'gender', 'category']],
                             use_container_width=True)
            else:
                st.info("Нет данных для отображения")

    with col3:
        csv_data = export_to_csv(st.session_state.annotations)
        if csv_data:
            timestamp = int(time.time())
            filename = f"annotations_{st.session_state.folder_name}_{timestamp}.csv"
            st.download_button(
                label="📥 Скачать CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.button("📥 Нет данных", disabled=True, use_container_width=True)


if __name__ == "__main__":
    main()