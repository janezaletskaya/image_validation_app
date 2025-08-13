import streamlit as st


def render_sidebar():
    """Рендерит боковую панель с навигацией и статистикой"""

    with st.sidebar:
        st.header("🧭 Навигация")

        # Навигация между изображениями (если загружены)
        if st.session_state.images_list:
            total_images = len(st.session_state.images_list)
            current_idx = st.session_state.current_image_index

            st.markdown(f"**Изображение {current_idx + 1} из {total_images}**")

            # Прогресс бар навигации
            progress = (current_idx + 1) / total_images
            st.progress(progress)

            # Быстрый переход
            new_index = st.selectbox(
                "Перейти к изображению:",
                range(total_images),
                index=current_idx,
                format_func=lambda
                    x: f"{x + 1}. {st.session_state.images_list[x][:30]}{'...' if len(st.session_state.images_list[x]) > 30 else ''}"
            )

            if new_index != current_idx:
                st.session_state.current_image_index = new_index
                st.rerun()

        # Статистика разметки
        if st.session_state.images_list:
            st.markdown("---")
            st.header("📊 Статистика")

            total_images = len(st.session_state.images_list)
            annotated_count = len(st.session_state.annotations)

            st.metric("Всего изображений", total_images)
            st.metric("Размечено", annotated_count)

            if total_images > 0:
                progress = annotated_count / total_images
                st.progress(progress)
                st.caption(f"{progress * 100:.1f}% завершено")

            # Показываем статистику по категориям
            if st.session_state.annotations:
                with st.expander("📈 Детальная статистика"):
                    from utils.annotations import get_annotation_stats
                    stats = get_annotation_stats()

                    col1, col2 = st.columns(2)

                    with col1:
                        st.metric("Валидных", stats['valid'])
                        st.metric("Невалидных", stats['invalid'])

                    with col2:
                        if stats['by_gender']:
                            st.markdown("**По полу:**")
                            for gender, count in stats['by_gender'].items():
                                st.text(f"{gender}: {count}")

                        if stats['by_category']:
                            st.markdown("**По категориям:**")
                            for category, count in stats['by_category'].items():
                                st.text(f"{category}: {count}")

        # Быстрые действия
        if st.session_state.images_list:
            st.markdown("---")
            st.header("⚡ Быстрые действия")

            # Переход к следующему неразмеченному
            unannotated_files = get_unannotated_files()
            if unannotated_files:
                if st.button("➡️ К неразмеченному", use_container_width=True):
                    next_idx = get_next_unannotated_index()
                    if next_idx is not None:
                        st.session_state.current_image_index = next_idx
                        st.rerun()

                st.caption(f"Осталось: {len(unannotated_files)} изображений")
            else:
                st.success("✅ Все изображения размечены!")

            # Очистка данных
            if st.button("🗑️ Очистить всё", use_container_width=True):
                if st.session_state.annotations:
                    st.session_state.annotations = []
                    st.success("Разметки очищены")
                    st.rerun()

            # Перезагрузка
            if st.button("🔄 Новый архив", use_container_width=True):
                # Очищаем все данные для загрузки нового архива
                for key in ['images_list', 'image_paths', 'annotations', 'folder_name', 'current_image_index']:
                    if key in st.session_state:
                        if key == 'current_image_index':
                            st.session_state[key] = 0
                        elif key in ['images_list', 'annotations']:
                            st.session_state[key] = []
                        elif key in ['image_paths']:
                            st.session_state[key] = {}
                        else:
                            st.session_state[key] = ""
                st.rerun()

        # Помощь и информация
        st.markdown("---")
        st.header("❓ Помощь")

        with st.expander("🔧 Горячие клавиши"):
            st.markdown("""
            **Навигация:**
            - `←` / `→` - Предыдущее/Следующее
            - `Ctrl + ←` / `Ctrl + →` - К началу/концу

            **Разметка:**
            - `V` - Валидно
            - `N` - Невалидно
            - `M` - Мужской
            - `F` - Женский
            """)

        with st.expander("📋 Формат CSV"):
            st.markdown("""
            **Столбцы выходного файла:**
            - `img_path` - путь к изображению
            - `validity` - валидность (Валидно/Невалидно)
            - `gender` - пол (М/Ж/М/Ж)
            - `category` - категория одежды

            **Пример:**
            ```
            img_path,validity,gender,category
            юбка/img1.jpg,Валидно,Ж,низ
            штаны/img2.jpg,Валидно,М,низ
            ```
            """)


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