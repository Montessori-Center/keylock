# models/keyword.py
from app import db
from datetime import datetime

class Campaign(db.Model):
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum('Enabled', 'Paused', 'Removed'), default='Enabled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    ad_groups = db.relationship('AdGroup', backref='campaign', lazy='dynamic')
    keywords = db.relationship('Keyword', backref='campaign', lazy='dynamic')

class AdGroup(db.Model):
    __tablename__ = 'ad_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Enum('Enabled', 'Paused', 'Removed'), default='Enabled')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    keywords = db.relationship('Keyword', backref='ad_group', lazy='dynamic')

class Keyword(db.Model):
    __tablename__ = 'keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    ad_group_id = db.Column(db.Integer, db.ForeignKey('ad_groups.id'), nullable=False)
    
    # Основные поля
    keyword = db.Column(db.String(500), nullable=False, index=True)
    criterion_type = db.Column(db.Enum('Phrase', 'Broad', 'Exact'), default='Phrase')
    max_cpc = db.Column(db.Numeric(10, 2))
    max_cpm = db.Column(db.Numeric(10, 2))
    max_cpv = db.Column(db.Numeric(10, 2))
    
    # Ставки
    first_page_bid = db.Column(db.Numeric(10, 2))
    top_of_page_bid = db.Column(db.Numeric(10, 2))
    first_position_bid = db.Column(db.Numeric(10, 2))
    
    # Качество
    quality_score = db.Column(db.Integer)
    landing_page_experience = db.Column(db.String(50))
    expected_ctr = db.Column(db.String(50))
    ad_relevance = db.Column(db.String(50))
    
    # URLs
    final_url = db.Column(db.Text)
    final_mobile_url = db.Column(db.Text)
    tracking_template = db.Column(db.Text)
    final_url_suffix = db.Column(db.String(255))
    custom_parameters = db.Column(db.Text)
    
    # Статусы
    status = db.Column(db.Enum('Enabled', 'Paused', 'Removed'), default='Enabled', index=True)
    approval_status = db.Column(db.String(50))
    
    # Пользовательские поля
    comment = db.Column(db.Text)
    has_ads = db.Column(db.Boolean, default=False)
    has_school_sites = db.Column(db.Boolean, default=False)
    has_google_maps = db.Column(db.Boolean, default=False)
    has_our_site = db.Column(db.Boolean, default=False)
    intent_type = db.Column(db.String(50))
    recommendation = db.Column(db.Text)
    
    # Метрики
    avg_monthly_searches = db.Column(db.Integer)
    three_month_change = db.Column(db.Numeric(10, 2))
    yearly_change = db.Column(db.Numeric(10, 2))
    competition = db.Column(db.String(50))
    competition_percent = db.Column(db.Numeric(5, 2))
    min_top_of_page_bid = db.Column(db.Numeric(10, 2))
    max_top_of_page_bid = db.Column(db.Numeric(10, 2))
    ad_impression_share = db.Column(db.Numeric(5, 2))
    organic_average_position = db.Column(db.Numeric(5, 2))
    organic_impression_share = db.Column(db.Numeric(5, 2))
    
    labels = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, fields=None):
        """Преобразование модели в словарь с выбором полей"""
        all_fields = {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'ad_group_id': self.ad_group_id,
            'keyword': self.keyword,
            'criterion_type': self.criterion_type,
            'max_cpc': float(self.max_cpc) if self.max_cpc else None,
            'max_cpm': float(self.max_cpm) if self.max_cpm else None,
            'max_cpv': float(self.max_cpv) if self.max_cpv else None,
            'first_page_bid': float(self.first_page_bid) if self.first_page_bid else None,
            'top_of_page_bid': float(self.top_of_page_bid) if self.top_of_page_bid else None,
            'first_position_bid': float(self.first_position_bid) if self.first_position_bid else None,
            'quality_score': self.quality_score,
            'landing_page_experience': self.landing_page_experience,
            'expected_ctr': self.expected_ctr,
            'ad_relevance': self.ad_relevance,
            'final_url': self.final_url,
            'final_mobile_url': self.final_mobile_url,
            'tracking_template': self.tracking_template,
            'final_url_suffix': self.final_url_suffix,
            'custom_parameters': self.custom_parameters,
            'status': self.status,
            'approval_status': self.approval_status,
            'comment': self.comment,
            'has_ads': self.has_ads,
            'has_school_sites': self.has_school_sites,
            'has_google_maps': self.has_google_maps,
            'has_our_site': self.has_our_site,
            'intent_type': self.intent_type,
            'recommendation': self.recommendation,
            'avg_monthly_searches': self.avg_monthly_searches,
            'three_month_change': float(self.three_month_change) if self.three_month_change else None,
            'yearly_change': float(self.yearly_change) if self.yearly_change else None,
            'competition': self.competition,
            'competition_percent': float(self.competition_percent) if self.competition_percent else None,
            'min_top_of_page_bid': float(self.min_top_of_page_bid) if self.min_top_of_page_bid else None,
            'max_top_of_page_bid': float(self.max_top_of_page_bid) if self.max_top_of_page_bid else None,
            'ad_impression_share': float(self.ad_impression_share) if self.ad_impression_share else None,
            'organic_average_position': float(self.organic_average_position) if self.organic_average_position else None,
            'organic_impression_share': float(self.organic_impression_share) if self.organic_impression_share else None,
            'labels': self.labels
        }
        
        if fields:
            return {k: all_fields[k] for k in fields if k in all_fields}
        return all_fields

class AppSetting(db.Model):
    __tablename__ = 'app_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text)  # Зашифрованное значение
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)