from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.repositories import (
    get_presets_by_user,
    get_preset_by_id,
    create_preset as create_preset_db,
    update_preset,
    delete_preset as delete_preset_db
)

presets_bp = Blueprint('presets', __name__)

@presets_bp.route('/')
@login_required
def list_presets():
    presets = get_presets_by_user(current_user.id)
    return render_template('presets_list.html', presets=presets)

@presets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_preset():
    if request.method == 'POST':
        name = request.form.get('name')
        model_name = request.form.get('model_name')
        system_prompt = request.form.get('system_prompt')
        
        try:
            temperature = float(request.form.get('temperature', 0.7))
            if not (0 <= temperature <= 1):
                raise ValueError
        except ValueError:
            flash('Температура має бути числом від 0 до 1.', 'danger')
            return render_template('preset_form.html')
        
        try:
            max_tokens = int(request.form.get('max_tokens', 512))
            if max_tokens <= 0:
                raise ValueError
        except ValueError:
            flash('Max токенів має бути додатним цілим числом.', 'danger')
            return render_template('preset_form.html')
        
        if not name or not name.strip():
            flash('Назва пресету обов\'язкова.', 'danger')
            return render_template('preset_form.html')
        
        create_preset_db(
            user_id=current_user.id,
            name=name,
            model_name=model_name or 'gemma3:1b',
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        flash('Пресет створено!', 'success')
        return redirect(url_for('presets.list_presets'))
    return render_template('preset_form.html')

@presets_bp.route('/<int:preset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_preset(preset_id):
    preset = get_preset_by_id(preset_id)
    if not preset:
        flash('Пресет не знайдено.', 'danger')
        return redirect(url_for('presets.list_presets'))
    if preset.user_id != current_user.id:
        flash('Недостатньо прав.', 'danger')
        return redirect(url_for('presets.list_presets'))

    if request.method == 'POST':
        name = request.form.get('name')
        model_name = request.form.get('model_name')
        system_prompt = request.form.get('system_prompt')
        
        try:
            temperature = float(request.form.get('temperature', 0.7))
            if not (0 <= temperature <= 1):
                raise ValueError
        except ValueError:
            flash('Температура має бути числом від 0 до 1.', 'danger')
            return render_template('preset_form.html', preset=preset)
        
        try:
            max_tokens = int(request.form.get('max_tokens', 512))
            if max_tokens <= 0:
                raise ValueError
        except ValueError:
            flash('Max токенів має бути додатним цілим числом.', 'danger')
            return render_template('preset_form.html', preset=preset)
        
        if not name or not name.strip():
            flash('Назва пресету обов\'язкова.', 'danger')
            return render_template('preset_form.html', preset=preset)
        
        update_preset(
            preset,
            name=name,
            model_name=model_name,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        flash('Пресет оновлено!', 'success')
        return redirect(url_for('presets.list_presets'))
    
    return render_template('preset_form.html', preset=preset)

@presets_bp.route('/<int:preset_id>/delete', methods=['POST'])
@login_required
def delete_preset(preset_id):
    preset = get_preset_by_id(preset_id)
    if not preset:
        flash('Пресет не знайдено.', 'danger')
        return redirect(url_for('presets.list_presets'))
    if preset.user_id != current_user.id:
        flash('Недостатньо прав.', 'danger')
        return redirect(url_for('presets.list_presets'))
    
    delete_preset_db(preset)
    flash('Пресет видалено.', 'success')
    return redirect(url_for('presets.list_presets'))