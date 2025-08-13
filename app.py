import streamlit as st
import pandas as pd
from components.sidebar import render_sidebar
from components.navigation import render_navigation
from components.annotation_form import render_annotation_form
from utils.annotations import export_to_csv
import time

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
if 'folder_name' not in st.session_state:
    st.session_state.folder_name = ""


def main():
    # Заголовок приложения
    st.title("🏷️ Разметка изображений Google Drive")
    st.markdown("*Быстрая разметка папки с изображениями одежды*")

    # Боковая панель
    render_sidebar()

    # Основной контент
    if not st.session_state.images_list or not st.session_state.folder_name:
        show_welcome_screen()
    else:
        show_annotation_interface()

    # Панель экспорта
    if st.session_state.annotations:
        show_export_panel()


def show_welcome_screen():
    """Показывает приветственный экран с инструкциями"""
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.info(
            "👆 **Начните работу:**\n1. Укажите ссылку на папку Google Drive\n2. Введите название категории\n3. Добавьте список файлов")

    with col2:
        st.markdown("### 📝 Пример:")
        st.code("""Ссылка: https://drive.google.com/drive/folders/1ABC...
Категория: юбка
Файлы:
img1.jpg
img2.png
фото3.jpeg""")

    # Инструкция по настройке Google Drive
    with st.expander("📖 Как настроить доступ к Google Drive"):
        st.markdown("""
        ### 🔧 Настройка папки на Google Drive:

        1. **Создайте/найдите папку** с изображениями одежды
        2. **Настройте доступ:**
           - Правый клик на папку → "Поделиться"
           - Измените на "Просмотр для всех, у кого есть ссылка"
           - Скопируйте ссылку
        3. **Получите список файлов:**
           - Откройте папку в браузере
           - Скопируйте названия файлов
        4. **Для показа изображений** понадобятся прямые ссылки на каждый файл

        ### 🖼️ Прямые ссылки на изображения:
        Формат: `https://drive.google.com/file/d/FILE_ID/preview`

        Где FILE_ID можно получить из ссылки на файл.
        """)


def show_annotation_interface():
    """Показывает интерфейс разметки"""
    st.markdown("---")

    # Навигация
    render_navigation()

    st.markdown("---")

    # Основной интерфейс разметки
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

    # Информация о файле
    st.info(f"📁 **Файл:** {filename}\n📂 **Папка:** {st.session_state.folder_name}")

    # Поле для прямой ссылки на изображение
    current_idx = st.session_state.current_image_index
    image_url = st.text_input(
        "🔗 Прямая ссылка на изображение:",
        placeholder="https://drive.google.com/file/d/FILE_ID/preview",
        help="Вставьте прямую ссылку для просмотра изображения",
        key=f"image_url_{current_idx}"
    )

    if image_url:
        try:
            st.image(image_url, use_column_width=True, caption=filename)
        except Exception as e:
            st.error(f"❌ Ошибка загрузки: {str(e)}")
            show_placeholder_image()
    else:
        show_placeholder_image()

        with st.expander("💡 Как получить прямую ссылку"):
            st.markdown("""
            **Быстрый способ:**
            1. Откройте файл в Google Drive
            2. Нажмите "Поделиться" → "Скопировать ссылку"
            3. Замените `/view?usp=sharing` на `/preview`

            **Пример:**
            - Было: `https://drive.google.com/file/d/1ABC.../view?usp=sharing`
            - Стало: `https://drive.google.com/file/d/1ABC.../preview`
            """)


def show_placeholder_image():
    """Показывает заглушку изображения"""
    st.image("https://via.placeholder.com/500x350/f8f9fa/6c757d?text=Изображение+не+загружено",
             use_column_width=True,
             caption="Введите прямую ссылку для просмотра")


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