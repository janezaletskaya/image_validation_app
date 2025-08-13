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

        # Автоматическое получение файлов
        if st.session_state.folder_name and folder_url:
            st.markdown("---")
            st.subheader("📁 Автозагрузка файлов")

            # Тестируем доступ к папке
            if st.button("🔍 Найти файлы автоматически", use_container_width=True):
                with st.spinner("Получаю список файлов из Google Drive..."):
                    try:
                        from utils.google_drive import (
                            test_folder_access,
                            cached_get_files_from_folder,
                            format_file_info,
                            validate_files_data
                        )

                        # Проверяем доступ
                        access_ok, access_msg = test_folder_access(folder_url)

                        if not access_ok:
                            st.error(f"❌ {access_msg}")
                            st.info("💡 Убедитесь что папка доступна 'всем, у кого есть ссылка'")
                        else:
                            # Получаем файлы
                            files_data = cached_get_files_from_folder(folder_url)

                            # Валидируем
                            is_valid, validation_msg = validate_files_data(files_data)

                            if is_valid:
                                # Сохраняем данные о файлах
                                st.session_state.files_data = files_data
                                filenames = [f['filename'] for f in files_data]
                                st.session_state.images_list = filenames
                                st.session_state.current_image_index = 0

                                st.success(f"✅ {validation_msg}")

                                # Показываем информацию
                                with st.expander("📋 Найденные файлы"):
                                    st.text(format_file_info(files_data))

                                st.rerun()
                            else:
                                st.error(f"❌ {validation_msg}")

                    except Exception as e:
                        st.error(f"❌ Ошибка: {str(e)}")
                        st.info("💡 Попробуйте ручной ввод файлов ниже")

            # Ручной ввод как запасной вариант
            with st.expander("📝 Ручной ввод файлов (если автозагрузка не работает)"):
                files_text = st.text_area(
                    "Названия файлов:",
                    placeholder="zr2509033501_262.jpg\nimage_001.png\nDSC_1234.jpeg",
                    height=150,
                    help="Введите по одному файлу на строку"
                )

                if st.button("✅ Загрузить вручную", use_container_width=True):
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