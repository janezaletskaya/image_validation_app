import streamlit as st


def render_navigation():
    """Рендерит навигацию между изображениями"""

    if not st.session_state.images_list:
        return

    total_images = len(st.session_state.images_list)
    current_idx = st.session_state.current_image_index
    current_filename = st.session_state.images_list[current_idx]

    # Основная навигация
    nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

    with nav_col1:
        if st.button("⬅️ Предыдущее", disabled=(current_idx == 0), use_container_width=True):
            st.session_state.current_image_index = max(0, current_idx - 1)
            st.rerun()

    with nav_col2:
        st.markdown(f"### 🖼️ {current_filename}")
        st.markdown(f"**Изображение {current_idx + 1} из {total_images}**")

        # Прогресс бар
        progress = (current_idx + 1) / total_images
        st.progress(progress)
        st.caption(f"Папка: {st.session_state.folder_name}")

    with nav_col3:
        if st.button("➡️ Следующее", disabled=(current_idx == total_images - 1), use_container_width=True):
            st.session_state.current_image_index = min(total_images - 1, current_idx + 1)
            st.rerun()

    # Дополнительная навигация
    render_quick_navigation(total_images, current_idx)
    render_keyboard_shortcuts()


def render_quick_navigation(total_images, current_idx):
    """Рендерит быструю навигацию"""

    st.markdown("#### 🧭 Быстрая навигация")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Слайдер для быстрого перехода
        new_index = st.slider(
            "Перейти к изображению:",
            min_value=0,
            max_value=total_images - 1,
            value=current_idx,
            format="Изображение %d"
        )

        if new_index != current_idx:
            st.session_state.current_image_index = new_index
            st.rerun()

    with col2:
        # Прямой ввод номера
        target_num = st.number_input(
            "Номер изображения:",
            min_value=1,
            max_value=total_images,
            value=current_idx + 1,
            step=1
        )

        target_index = target_num - 1
        if target_index != current_idx:
            st.session_state.current_image_index = target_index
            st.rerun()


def render_keyboard_shortcuts():
    """Показывает информацию о горячих клавишах"""

    with st.expander("⌨️ Горячие клавиши"):
        st.markdown("""
        **Навигация:**
        - `←` / `→` - Предыдущее/Следующее изображение
        - `Ctrl + ←` / `Ctrl + →` - К началу/концу списка

        **Разметка:**
        - `1` - Валидно
        - `2` - Невалидно  
        - `M` - Мужской
        - `F` - Женский
        - `Ctrl + S` - Сохранить разметку

        *Примечание: горячие клавиши работают при фокусе на странице*
        """)


def render_annotation_status():
    """Показывает статус разметки для текущего изображения"""

    if not st.session_state.images_list:
        return

    current_filename = st.session_state.images_list[st.session_state.current_image_index]

    # Проверяем, есть ли разметка для текущего изображения
    current_annotation = None
    for ann in st.session_state.annotations:
        if ann['filename'] == current_filename:
            current_annotation = ann
            break

    if current_annotation:
        st.success("✅ Изображение размечено")
    else:
        st.warning("⚠️ Изображение не размечено")


def get_navigation_stats():
    """Возвращает статистику навигации"""

    if not st.session_state.images_list:
        return {}

    total = len(st.session_state.images_list)
    current = st.session_state.current_image_index + 1
    annotated = len(st.session_state.annotations)
    remaining = total - annotated

    return {
        'total': total,
        'current': current,
        'annotated': annotated,
        'remaining': remaining,
        'progress_percent': (annotated / total) * 100 if total > 0 else 0
    }