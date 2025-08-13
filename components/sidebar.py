import streamlit as st
from utils.helpers import extract_folder_name_from_url


def render_sidebar():
    """Рендерит боковую панель с настройками"""

    with st.sidebar:
        st.header("📂 Настройка папки")

        # Инструкция
        with st.expander("📖 Как использовать"):
            st.markdown("""
            **Шаги:**
            1. Вставьте ссылку на папку Google Drive
            2. Укажите категорию (название папки)  
            3. Введите список файлов изображений
            4. Начните разметку!

            **Требования:**
            - Папка должна быть доступна по ссылке
            - Нужны названия всех файлов изображений
            """)

        # Ссылка на папку
        folder_url = st.text_input(
            "🔗 Ссылка на папку:",
            placeholder="https://drive.google.com/drive/folders/1ABC...",
            help="Ссылка на папку Google Drive с изображениями"
        )

        # Автоматическое извлечение названия или ручной ввод
        auto_name = extract_folder_name_from_url(folder_url) if folder_url else ""
        folder_name = st.text_input(
            "📁 Категория одежды:",
            value=auto_name,
            placeholder="юбка, штаны, шорты, шляпа...",
            help="Название категории для разметки"
        )

        if folder_name:
            st.session_state.folder_name = folder_name

        # Список файлов
        if st.session_state.folder_name:
            st.markdown("---")
            st.subheader("📝 Список файлов")

            files_text = st.text_area(
                f"Файлы в папке '{st.session_state.folder_name}':",
                placeholder="img1.jpg\nimg2.png\nфото3.jpeg\nDSC_001.jpg",
                height=200,
                help="Введите по одному файлу на строку"
            )

            if st.button("✅ Загрузить файлы", use_container_width=True):
                if files_text.strip():
                    filenames = [f.strip() for f in files_text.split('\n') if f.strip()]
                    # Фильтруем только файлы изображений
                    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
                    valid_files = []

                    for filename in filenames:
                        if any(filename.lower().endswith(ext) for ext in image_extensions):
                            valid_files.append(filename)

                    if valid_files:
                        st.session_state.images_list = valid_files
                        st.session_state.current_image_index = 0
                        st.success(f"✅ Загружено {len(valid_files)} изображений")
                        st.rerun()
                    else:
                        st.error("❌ Не найдено файлов изображений")
                else:
                    st.error("❌ Введите список файлов")

        # Статистика (если есть загруженные файлы)
        if st.session_state.images_list:
            st.markdown("---")
            st.subheader("📊 Статистика")

            total_images = len(st.session_state.images_list)
            annotated_count = len(st.session_state.annotations)

            st.metric("Всего изображений", total_images)
            st.metric("Размечено", annotated_count)

            if total_images > 0:
                progress = annotated_count / total_images
                st.progress(progress)
                st.caption(f"{progress * 100:.1f}% завершено")

            # Быстрые действия
            st.markdown("**🔧 Действия:**")

            if st.button("🗑️ Очистить все разметки", use_container_width=True):
                if st.session_state.annotations:
                    st.session_state.annotations = []
                    st.success("Разметки очищены")
                    st.rerun()

            if st.button("🔄 Перезагрузить список", use_container_width=True):
                st.session_state.images_list = []
                st.session_state.current_image_index = 0
                st.rerun()

        # Информация о текущей сессии
        if st.session_state.folder_name:
            st.markdown("---")
            st.caption("ℹ️ **Текущая сессия:**")
            st.caption(f"Папка: {st.session_state.folder_name}")
            if st.session_state.images_list:
                current_file = st.session_state.images_list[st.session_state.current_image_index]
                st.caption(f"Файл: {current_file}")