from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
from models import UserSetting, get_global_setting
from utils import login_required, get_current_user

settings_bp = Blueprint(
    'settings',
    __name__,
    template_folder='templates',
    url_prefix='/settings'
)


#--------------------------------HELPER FUNCTIONS--------------------------------

def get_or_create_user_setting(user):
    user_setting, created = UserSetting.get_or_create(user=user)
    return user_setting


def extract_theme_from_form(form_data):
    theme = form_data.get('theme', 'light')
    allowed_themes = ['light', 'dark']
    return theme if theme in allowed_themes else 'light'


def extract_gst_settings_from_form(form_data):
    apply_gst = form_data.get('apply_gst') == 'on'
    
    try:
        gst_percent = float(form_data.get('gst_percent', 18))
        if gst_percent < 0 or gst_percent > 100:
            gst_percent = 18  
    except (TypeError, ValueError):
        gst_percent = 18  
    
    return apply_gst, gst_percent


def update_user_theme(user_setting, theme):
    user_setting.theme = theme
    user_setting.save()


def update_global_gst_settings(global_setting, apply_gst, gst_percent):
    global_setting.apply_gst = apply_gst
    global_setting.gst_percent = gst_percent
    global_setting.updated_at = datetime.now()
    global_setting.save()


def process_settings_form(form_data, user_setting, global_setting):
    """Process and save settings from form data"""
    # Update theme
    theme = extract_theme_from_form(form_data)
    update_user_theme(user_setting, theme)
    
    # Update GST settings
    apply_gst, gst_percent = extract_gst_settings_from_form(form_data)
    update_global_gst_settings(global_setting, apply_gst, gst_percent)


#--------------------------------ROUTE HANDLERS--------------------------------

@settings_bp.route('/', methods=['GET', 'POST'])
@login_required
def settings_page():
    """Render and handle settings page"""
    user = get_current_user()
    user_setting = get_or_create_user_setting(user)
    global_setting = get_global_setting()
    
    if request.method == "POST":
        try:
            process_settings_form(request.form, user_setting, global_setting)
            flash("Settings updated successfully!", "settings_success")
            return redirect(url_for('settings.settings_page'))
        
        except Exception as e:
            flash(f"Error updating settings: {str(e)}", "error")
            return redirect(url_for('settings.settings_page'))
    
    return render_template(
        'settings.html',
        user_setting=user_setting,
        global_setting=global_setting
    )