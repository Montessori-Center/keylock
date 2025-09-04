# api/settings.py
from flask import Blueprint, request, jsonify
from app import db
from models.keyword import AppSetting
from services.encryption import encryption_service

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/get', methods=['GET'])
def get_settings():
    """Получение настроек приложения"""
    try:
        settings = AppSetting.query.all()
        decrypted_settings = {}
        
        for setting in settings:
            try:
                decrypted_settings[setting.setting_key] = encryption_service.decrypt(setting.setting_value)
            except:
                # Если не можем расшифровать, возвращаем как есть
                decrypted_settings[setting.setting_key] = setting.setting_value
        
        return jsonify({
            'success': True,
            'settings': decrypted_settings
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@settings_bp.route('/save', methods=['POST'])
def save_settings():
    """Сохранение настроек приложения"""
    try:
        data = request.json
        
        for key, value in data.items():
            # Шифруем значение
            encrypted_value = encryption_service.encrypt(value)
            
            # Ищем существующую настройку или создаем новую
            setting = AppSetting.query.filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = encrypted_value
            else:
                setting = AppSetting(
                    setting_key=key,
                    setting_value=encrypted_value
                )
                db.session.add(setting)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500