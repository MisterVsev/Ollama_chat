from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/install-guide')
def install_guide():
    return render_template('install_guide.html')