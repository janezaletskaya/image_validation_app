import streamlit as st


def render_navigation():
    """Рендерит компактную навигацию между изображениями"""

    if not st.session_state.images_list:
        return

    total_images = len(st.session_state.images_list)
    current_idx = st.session_state.current_image_index
    current_filename = st.session_state.images_list[current_idx]

    # Компактная навигация
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("⬅️ Предыдущее", disabled=(current_idx == 0), use_container_width=True):
            st.session_state.current_image_index = max(0, current_idx - 1)
            st.rerun()

    with col2:
        st.markdown(f"**Изображение {current_idx + 1} из {total_images}**")
        # Простой прогресс бар
        progress = (current_idx + 1) / total_images
        st.progress(progress)

    with col3:
        if st.button("➡️ Следующее", disabled=(current_idx == total_images - 1), use_container_width=True):
            st.session_state.current_image_index = min(total_images - 1, current_idx + 1)
            st.rerun()


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