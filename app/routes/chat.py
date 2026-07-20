import requests
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Conversation, Message, ModelPreset

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/')
@login_required
def chat_view():
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(
        Conversation.updated_at.desc()).all()
    presets = ModelPreset.query.filter_by(user_id=current_user.id).all()
    return render_template('chat.html', conversations=conversations, presets=presets)

@chat_bp.route('/new', methods=['POST'])
@login_required
def new_conversation():
    preset_id = request.form.get('preset_id')
    if preset_id:
        preset = ModelPreset.query.get_or_404(preset_id)
        if preset.user_id != current_user.id:
            flash('Недостатньо прав.', 'danger')
            return redirect(url_for('chat.chat_view'))
    else:
        preset = None

    conv = Conversation(user_id=current_user.id, preset_id=preset_id)
    db.session.add(conv)
    db.session.commit()
    return redirect(url_for('chat.chat_view', conv_id=conv.id))

@chat_bp.route('/<int:conv_id>')
@login_required
def chat_detail(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if conv.user_id != current_user.id:
        flash('Це не ваш діалог.', 'danger')
        return redirect(url_for('chat.chat_view'))
    conversations = Conversation.query.filter_by(user_id=current_user.id).order_by(
        Conversation.updated_at.desc()).all()
    presets = ModelPreset.query.filter_by(user_id=current_user.id).all()
    messages = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at).all()
    return render_template('chat.html', conversations=conversations, presets=presets,
                           current_conv=conv, messages=messages)

@chat_bp.route('/<int:conv_id>/send', methods=['POST'])
@login_required
def send_message(conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if conv.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403

    user_message = request.form.get('message')
    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    msg_user = Message(conversation_id=conv.id, role='user', content=user_message)
    db.session.add(msg_user)
    db.session.commit()

    history = Message.query.filter_by(conversation_id=conv.id).order_by(Message.created_at).all()

    system_prompt = None
    if conv.preset_id:
        preset = ModelPreset.query.get(conv.preset_id)
        if preset and preset.system_prompt:
            system_prompt = preset.system_prompt

    ollama_url = current_app.config['OLLAMA_API_URL']
    model_name = conv.preset.model_name if conv.preset else current_app.config['DEFAULT_MODEL']

    full_prompt = ""
    if system_prompt:
        full_prompt += system_prompt + "\n\n"
    for msg in history:
        if msg.role == 'user':
            full_prompt += f"User: {msg.content}\n"
        else:
            full_prompt += f"Assistant: {msg.content}\n"
    full_prompt += f"User: {user_message}\nAssistant:"

    temperature = conv.preset.temperature if conv.preset else 0.7
    max_tokens = conv.preset.max_tokens if conv.preset else 512

    payload = {
        "model": model_name,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    try:
        response = requests.post(ollama_url, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        assistant_reply = data.get('response', '').strip()
    except Exception as e:
        flash(f'Помилка при зверненні до Ollama: {e}', 'danger')
        return redirect(url_for('chat.chat_detail', conv_id=conv.id))

    msg_assistant = Message(conversation_id=conv.id, role='assistant', content=assistant_reply)
    db.session.add(msg_assistant)
    conv.updated_at = db.func.now()
    db.session.commit()

    if not conv.title and len(history) <= 1:
        words = user_message.split()[:5]
        conv.title = ' '.join(words) + ('...' if len(user_message.split()) > 5 else '')
        db.session.commit()

    return redirect(url_for('chat.chat_detail', conv_id=conv.id))