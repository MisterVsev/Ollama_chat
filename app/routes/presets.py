from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import ModelPreset

presets_bp = Blueprint('presets', __name__)

@presets_bp.route('/')
@login_required
def list_presets():
    presets = ModelPreset.query.filter_by(user_id=current_user.id).all()
    return render_template('presets_list.html', presets=presets)

@presets_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_preset():
    if request.method == 'POST':
        name = request.form.get('name')
        model_name = request.form.get('model_name')
        system_prompt = request.form.get('system_prompt')
        temperature = float(request.form.get('temperature', 0.7))
        max_tokens = int(request.form.get('max_tokens', 512))

        if not name:
            flash('Назва обов’язкова.', 'danger')
            return render_template('preset_form.html')

        preset = ModelPreset(
            user_id=current_user.id,
            name=name,
            model_name=model_name or 'gemma3:1b',
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        db.session.add(preset)
        db.session.commit()
        flash('Пресет створено!', 'success')
        return redirect(url_for('presets.list_presets'))
    return render_template('preset_form.html')

@presets_bp.route('/<int:preset_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_preset(preset_id):
    preset = ModelPreset.query.get_or_404(preset_id)
    if preset.user_id != current_user.id:
        flash('Недостатньо прав.', 'danger')
        return redirect(url_for('presets.list_presets'))

    if request.method == 'POST':
        preset.name = request.form.get('name')
        preset.model_name = request.form.get('model_name')
        preset.system_prompt = request.form.get('system_prompt')
        preset.temperature = float(request.form.get('temperature', 0.7))
        preset.max_tokens = int(request.form.get('max_tokens', 512))
        db.session.commit()
        flash('Пресет оновлено!', 'success')
        return redirect(url_for('presets.list_presets'))
    return render_template('preset_form.html', preset=preset)

@presets_bp.route('/<int:preset_id>/delete', methods=['POST'])
@login_required
def delete_preset(preset_id):
    preset = ModelPreset.query.get_or_404(preset_id)
    if preset.user_id != current_user.id:
        flash('Недостатньо прав.', 'danger')
        return redirect(url_for('presets.list_presets'))
    db.session.delete(preset)
    db.session.commit()
    flash('Пресет видалено.', 'success')
    return redirect(url_for('presets.list_presets'))