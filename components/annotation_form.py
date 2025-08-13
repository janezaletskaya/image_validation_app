import streamlit as st
from utils.annotations import save_annotation, get_current_annotation


def render_annotation_form(filename):
    """Рендерит форму разметки для изображения"""

    st.markdown("### 🏷️ Разметка")

    # Получаем текущую разметку
    current_annotation = get_current_annotation(filename)

    # Показываем статус
    if current_annotation:
        st.success("✅ Изображение размечено")
    else:
        st.info("⏳ Требует разметки")

    # Форма разметки
    with st.form(key=f"annotation_form_{st.session_state.current_image_index}"):

        # 1. Валидность (обязательное поле)
        st.markdown("#### 📋 Валидность")
        validity = st.radio(
            "Подходит ли изображение для обучения модели?",
            ["Валидно", "Невалидно"],
            index=0 if not current_annotation else (0 if current_annotation['validity'] == 'Валидно' else 1),
            help="Валидно = изображение четкое, подходящее для обучения"
        )

        # 2. Пол (можно выбрать несколько)
        st.markdown("#### 👥 Пол")
        col1, col2 = st.columns(2)

        with col1:
            gender_m = st.checkbox(
                "Мужской (М)",
                value=current_annotation and 'М' in current_annotation['gender'] if current_annotation else False,
                help="Одежда для мужчин"
            )

        with col2:
            gender_f = st.checkbox(
                "Женский (Ж)",
                value=current_annotation and 'Ж' in current_annotation['gender'] if current_annotation else False,
                help="Одежда для женщин"
            )

        # Формируем строку пола
        gender_list = []
        if gender_m:
            gender_list.append("М")
        if gender_f:
            gender_list.append("Ж")
        gender = "/".join(gender_list) if gender_list else ""

        # 3. Категория одежды (обязательное поле)
        st.markdown("#### 👔 Категория одежды")
        category = st.radio(
            "К какой категории относится одежда на изображении?",
            ["верх", "низ", "обувь", "голова", "аксессуар"],
            index=get_category_index(current_annotation),
            help="Выберите основную категорию одежды"
        )

        # Дополнительные поля (опционально)
        with st.expander("🔧 Дополнительные настройки"):
            notes = st.text_area(
                "Заметки (опционально):",
                value=current_annotation.get('notes', '') if current_annotation else '',
                placeholder="Дополнительные комментарии...",
                help="Любые дополнительные заметки о изображении"
            )

        # Кнопки действий
        col1, col2 = st.columns(2)

        with col1:
            submit_button = st.form_submit_button("💾 Сохранить", use_container_width=True)

        with col2:
            clear_button = st.form_submit_button("🗑️ Очистить", use_container_width=True)

        # Обработка отправки формы
        if submit_button:
            handle_form_submission(filename, validity, gender, category, notes)

        if clear_button:
            handle_clear_annotation(filename)

    # Показываем текущую разметку
    if current_annotation:
        show_current_annotation(current_annotation)

    # Быстрые действия
    render_quick_actions(filename)

    # Дополнительные возможности
    render_annotation_shortcuts()
    render_batch_actions()
    render_annotation_statistics()
    render_validation_warnings()


def get_category_index(current_annotation):
    """Возвращает индекс текущей категории"""
    categories = ["верх", "низ", "обувь", "голова", "аксессуар"]

    if not current_annotation:
        return 0

    try:
        return categories.index(current_annotation['category'])
    except (ValueError, KeyError):
        return 0


def handle_form_submission(filename, validity, gender, category, notes=""):
    """Обрабатывает отправку формы разметки"""

    # Валидация
    if not gender:
        st.error("❌ Выберите хотя бы один пол (М или Ж)")
        return

    # Сохраняем разметку
    try:
        success = save_annotation(filename, validity, gender, category, st.session_state.folder_name, notes)

        if success:
            st.success("✅ Разметка сохранена!")

            # Переходим к следующему изображению, если это не последнее
            if st.session_state.current_image_index < len(st.session_state.images_list) - 1:
                st.session_state.current_image_index += 1
                st.rerun()
        else:
            st.error("❌ Ошибка при сохранении разметки")

    except Exception as e:
        st.error(f"❌ Ошибка: {str(e)}")


def handle_clear_annotation(filename):
    """Обрабатывает очистку разметки"""

    # Удаляем разметку для текущего файла
    st.session_state.annotations = [
        ann for ann in st.session_state.annotations
        if ann['filename'] != filename
    ]

    st.success("🗑️ Разметка очищена")
    st.rerun()


def show_current_annotation(annotation):
    """Показывает текущую разметку"""

    st.markdown("---")
    st.markdown("#### 📋 Текущая разметка:")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Валидность", annotation['validity'])
        st.metric("Пол", annotation['gender'])

    with col2:
        st.metric("Категория", annotation['category'])
        if annotation.get('notes'):
            st.caption(f"Заметки: {annotation['notes']}")


def render_quick_actions(filename):
    """Рендерит быстрые действия"""

    st.markdown("---")
    st.markdown("#### ⚡ Быстрые действия")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✅ Валидно + Ж + верх", use_container_width=True):
            save_annotation(filename, "Валидно", "Ж", "верх", st.session_state.folder_name)
            advance_to_next()

    with col2:
        if st.button("✅ Валидно + Ж + низ", use_container_width=True):
            save_annotation(filename, "Валидно", "Ж", "низ", st.session_state.folder_name)
            advance_to_next()

    with col3:
        if st.button("❌ Невалидно", use_container_width=True):
            save_annotation(filename, "Невалидно", "Ж", "верх", st.session_state.folder_name)
            advance_to_next()


def advance_to_next():
    """Переходит к следующему изображению"""
    if st.session_state.current_image_index < len(st.session_state.images_list) - 1:
        st.session_state.current_image_index += 1
        st.rerun()


def render_annotation_shortcuts():
    """Показывает горячие клавиши для разметки"""

    with st.expander("⌨️ Горячие клавиши для разметки"):
        st.markdown("""
        **Валидность:**
        - `V` - Валидно
        - `N` - Невалидно

        **Пол:**
        - `M` - Мужской
        - `F` - Женский

        **Категория:**
        - `1` - верх
        - `2` - низ  
        - `3` - обувь
        - `4` - голова
        - `5` - аксессуар

        **Действия:**
        - `Ctrl + S` - Сохранить
        - `Ctrl + D` - Очистить
        - `Space` - Следующее изображение
        - `Enter` - Сохранить и перейти к следующему
        """)


def render_batch_actions():
    """Рендерит действия для массовой обработки"""

    with st.expander("🔄 Массовые действия"):
        st.markdown("**Применить ко всем неразмеченным изображениям:**")

        col1, col2 = st.columns(2)

        with col1:
            batch_validity = st.selectbox(
                "Валидность:",
                ["Не применять", "Валидно", "Невалидно"]
            )

            batch_gender = st.selectbox(
                "Пол:",
                ["Не применять", "М", "Ж", "М/Ж"]
            )

        with col2:
            batch_category = st.selectbox(
                "Категория:",
                ["Не применять", "верх", "низ", "обувь", "голова", "аксессуар"]
            )

        if st.button("🚀 Применить массово", use_container_width=True):
            apply_batch_annotation(batch_validity, batch_gender, batch_category)


def apply_batch_annotation(validity, gender, category):
    """Применяет разметку ко всем неразмеченным изображениям"""

    # Получаем список неразмеченных файлов
    annotated_files = {ann['filename'] for ann in st.session_state.annotations}
    unannotated_files = [
        filename for filename in st.session_state.images_list
        if filename not in annotated_files
    ]

    if not unannotated_files:
        st.warning("⚠️ Все изображения уже размечены")
        return

    applied_count = 0

    for filename in unannotated_files:
        # Используем текущие значения или значения по умолчанию
        use_validity = validity if validity != "Не применять" else "Валидно"
        use_gender = gender if gender != "Не применять" else "Ж"
        use_category = category if category != "Не применять" else "верх"

        success = save_annotation(
            filename,
            use_validity,
            use_gender,
            use_category,
            st.session_state.folder_name
        )

        if success:
            applied_count += 1

    if applied_count > 0:
        st.success(f"✅ Применено к {applied_count} изображениям")
        st.rerun()
    else:
        st.error("❌ Не удалось применить разметку")


def render_annotation_statistics():
    """Показывает статистику текущих разметок"""

    if not st.session_state.annotations:
        return

    with st.expander("📊 Статистика разметок"):
        from utils.annotations import get_annotation_stats
        stats = get_annotation_stats()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Всего размечено", stats['total'])
            st.metric("Валидных", stats['valid'])
            st.metric("Невалидных", stats['invalid'])

        with col2:
            st.markdown("**По полу:**")
            for gender, count in stats['by_gender'].items():
                st.text(f"{gender}: {count}")

        with col3:
            st.markdown("**По категориям:**")
            for category, count in stats['by_category'].items():
                st.text(f"{category}: {count}")


def render_validation_warnings():
    """Показывает предупреждения о качестве разметки"""

    if not st.session_state.annotations:
        return

    warnings = []

    # Проверяем баланс валидных/невалидных
    valid_count = sum(1 for ann in st.session_state.annotations if ann['validity'] == 'Валидно')
    invalid_count = len(st.session_state.annotations) - valid_count

    if invalid_count > valid_count * 0.5:  # Если невалидных больше 50%
        warnings.append("⚠️ Много невалидных изображений - проверьте качество данных")

    # Проверяем распределение по категориям
    from collections import Counter
    category_counts = Counter(ann['category'] for ann in st.session_state.annotations)
    max_count = max(category_counts.values()) if category_counts else 0
    min_count = min(category_counts.values()) if category_counts else 0

    if max_count > min_count * 3:  # Если дисбаланс больше 3:1
        warnings.append("⚠️ Неравномерное распределение по категориям")

    if warnings:
        with st.expander("⚠️ Предупреждения качества"):
            for warning in warnings:
                st.warning(warning)


def get_annotation_progress():
    """Возвращает прогресс разметки"""

    if not st.session_state.images_list:
        return 0, 0, 0

    total = len(st.session_state.images_list)
    annotated = len(st.session_state.annotations)
    remaining = total - annotated

    return total, annotated, remaining