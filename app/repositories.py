from app import db
from app.models import User, ModelPreset, Conversation, Message
from werkzeug.security import generate_password_hash
from flask import render_template, flash

def create_user_with_password(username, email, password, bio):
    password_hash = generate_password_hash(password)
    user = User(username=username, email=email, password_hash=password_hash, bio=bio)
    if email and email.strip():
        if get_user_by_email(email):
            flash('Email уже используется.', 'danger')
            return render_template('register.html')
    else:
        email = None
    if email == ' ':
        email = None
    db.session.add(user)
    db.session.commit()
    return user

def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

def get_user_by_email(email):
    return User.query.filter_by(email=email).first()

def create_user(username, email, password_hash, bio):
    user = User(username=username, email=email, password_hash=password_hash, bio=bio)
    db.session.add(user)
    db.session.commit()
    return user


def get_presets_by_user(user_id):
    return ModelPreset.query.filter_by(user_id=user_id).all()

def get_preset_by_id(preset_id):
    return ModelPreset.query.get(preset_id)

def create_preset(user_id, name, model_name, system_prompt, temperature, max_tokens):
    preset = ModelPreset(
        user_id=user_id,
        name=name,
        model_name=model_name,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens
    )
    db.session.add(preset)
    db.session.commit()
    return preset

def update_preset(preset, name, model_name, system_prompt, temperature, max_tokens):
    preset.name = name
    preset.model_name = model_name
    preset.system_prompt = system_prompt
    preset.temperature = temperature
    preset.max_tokens = max_tokens
    db.session.commit()

def delete_preset(preset):
    db.session.delete(preset)
    db.session.commit()


def get_conversations_by_user(user_id):
    return Conversation.query.filter_by(user_id=user_id).order_by(Conversation.updated_at.desc()).all()

def get_conversation_by_id(conv_id):
    return Conversation.query.get(conv_id)

def create_conversation(user_id, preset_id=None):
    conv = Conversation(user_id=user_id, preset_id=preset_id)
    db.session.add(conv)
    db.session.commit()
    return conv

def update_conversation_title(conv, title):
    conv.title = title
    db.session.commit()

def update_conversation_timestamp(conv):
    conv.updated_at = db.func.now()
    db.session.commit()


def get_messages_by_conversation(conv_id):
    return Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at).all()

def create_message(conversation_id, role, content):
    msg = Message(conversation_id=conversation_id, role=role, content=content)
    db.session.add(msg)
    db.session.commit()
    return msg