import requests
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.repositories import get_conversations_by_user, get_conversation_by_id, create_conversation, update_conversation_title, update_conversation_timestamp, get_messages_by_conversation, create_message

from app.models import ModelPreset

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def chat_view():
    conversations = get_conversations_by_user(current_user.id)
    presets = ModelPreset.query.filter_by(user_id=current_user.id).all()  # можно тоже вынести в репозиторий, но пока оставим
    return render_template('chat.html', conversations=conversations, presets=presets)

@chat_bp.route('/new', methods=['POST'])
@login_required
def new_conversation():
    preset_id = request.form.get('preset_id')
    if preset_id:
        preset = ModelPreset.query.get(preset_id)
        if not preset or preset.user_id != current_user.id:
            flash('Недостатньо прав.', 'danger')
            return redirect(url_for('chat.chat_view'))
    conv = create_conversation(current_user.id, preset_id)
    return redirect(url_for('chat.chat_detail', conv_id=conv.id))

@chat_bp.route('/<int:conv_id>')
@login_required
def chat_detail(conv_id):
    conv = get_conversation_by_id(conv_id)
    if not conv or conv.user_id != current_user.id:
        flash('Це не ваш діалог.', 'danger')
        return redirect(url_for('chat.chat_view'))
    conversations = get_conversations_by_user(current_user.id)
    presets = ModelPreset.query.filter_by(user_id=current_user.id).all()
    messages = get_messages_by_conversation(conv_id)
    return render_template('chat.html', conversations=conversations, presets=presets,
                           current_conv=conv, messages=messages)

@chat_bp.route('/<int:conv_id>/send', methods=['POST'])
@login_required
def send_message(conv_id):
    conv = get_conversation_by_id(conv_id)
    if not conv or conv.user_id != current_user.id:
        flash('Діалог не знайдено.', 'danger')
        return redirect(url_for('chat.chat_view'))

    user_message = request.form.get('message')
    if not user_message:
        flash('Повідомлення не може бути порожнім.', 'danger')
        return redirect(url_for('chat.chat_detail', conv_id=conv.id))

    create_message(conv_id, 'user', user_message)

    # Формируем запрос к Ollama с учётом bio пользователя
    system_prompt = None
    if conv.preset_id:
        preset = ModelPreset.query.get(conv.preset_id)
        if preset and preset.system_prompt:
            system_prompt = preset.system_prompt

    full_prompt = ""
    if current_user.bio:
        full_prompt += f"Информация о пользователе: {current_user.bio}\n\n"
    if system_prompt:
        full_prompt += system_prompt + "\n\n"

    history = get_messages_by_conversation(conv_id)
    for msg in history:
        if msg.role == 'user':
            full_prompt += f"User: {msg.content}\n"
        else:
            full_prompt += f"Assistant: {msg.content}\n"
    full_prompt += f"User: {user_message}\nAssistant:"

    model_name = preset.model_name if conv.preset_id and preset else current_app.config['DEFAULT_MODEL']
    temperature = preset.temperature if conv.preset_id and preset else 0.7
    max_tokens = preset.max_tokens if conv.preset_id and preset else 512

    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens}
    }
    try:
        response = requests.post(current_app.config['OLLAMA_API_URL'], json=payload, timeout=60)
        response.raise_for_status()
        assistant_reply = response.json().get('response', '').strip()
    except Exception as e:
        flash(f'Помилка при зверненні до Ollama: {e}', 'danger')
        return redirect(url_for('chat.chat_detail', conv_id=conv.id))

    create_message(conv_id, 'assistant', assistant_reply)
    update_conversation_timestamp(conv)

    if not conv.title:
        words = user_message.split()[:5]
        conv.title = ' '.join(words) + ('...' if len(user_message.split()) > 5 else '')
        update_conversation_title(conv, conv.title)

    return redirect(url_for('chat.chat_detail', conv_id=conv.id))