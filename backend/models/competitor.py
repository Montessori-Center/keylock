# backend/models/competitor.py
from app import db
from datetime import datetime

class CompetitorSchool(db.Model):
    """Модель для школ-конкурентов"""
    __tablename__ = 'competitor_schools'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    org_type = db.Column(
        db.Enum('Школа', 'База репетиторов', 'Не школа', 'Партнёр'),
        default='Школа'
    )
    competitiveness = db.Column(db.Integer, default=0, comment='Частота появлений в SERP')
    last_seen_at = db.Column(db.DateTime, nullable=True, comment='Последнее появление в SERP')
    notes = db.Column(db.Text, comment='Заметки пользователя')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Преобразование в словарь для JSON"""
        return {
            'id': self.id,
            'domain': self.domain,
            'org_type': self.org_type,
            'competitiveness': self.competitiveness,
            'last_seen_at': self.last_seen_at.isoformat() if self.last_seen_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SerpAnalysisHistory(db.Model):
    """История SERP-анализов"""
    __tablename__ = 'serp_analysis_history'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('keywords.id'), nullable=False)
    keyword_text = db.Column(db.String(500), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    has_ads = db.Column(db.Boolean, default=False)
    has_maps = db.Column(db.Boolean, default=False)
    has_our_site = db.Column(db.Boolean, default=False)
    has_school_sites = db.Column(db.Boolean, default=False)
    intent_type = db.Column(db.String(50))
    organic_count = db.Column(db.Integer, default=0)
    paid_count = db.Column(db.Integer, default=0)
    maps_count = db.Column(db.Integer, default=0)
    school_percentage = db.Column(db.Numeric(5, 2), default=0)
    cost = db.Column(db.Numeric(10, 4), default=0)
    parsed_items = db.Column(db.JSON, comment='JSON с детальными данными')
    analysis_result = db.Column(db.JSON, comment='JSON с результатами анализа')
    
    def to_dict(self):
        return {
            'id': self.id,
            'keyword_id': self.keyword_id,
            'keyword_text': self.keyword_text,
            'campaign_id': self.campaign_id,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'has_ads': self.has_ads,
            'has_maps': self.has_maps,
            'has_our_site': self.has_our_site,
            'has_school_sites': self.has_school_sites,
            'intent_type': self.intent_type,
            'organic_count': self.organic_count,
            'paid_count': self.paid_count,
            'maps_count': self.maps_count,
            'school_percentage': float(self.school_percentage) if self.school_percentage else 0,
            'cost': float(self.cost) if self.cost else 0,
            'parsed_items': self.parsed_items,
            'analysis_result': self.analysis_result
        }


class SerpCompetitorAppearance(db.Model):
    """Появления конкурентов в SERP-анализах"""
    __tablename__ = 'serp_competitor_appearances'
    
    id = db.Column(db.Integer, primary_key=True)
    serp_analysis_id = db.Column(db.Integer, db.ForeignKey('serp_analysis_history.id'), nullable=False)
    competitor_id = db.Column(db.Integer, db.ForeignKey('competitor_schools.id'), nullable=False)
    position = db.Column(db.Integer, comment='Позиция в выдаче')
    result_type = db.Column(db.Enum('organic', 'paid', 'maps'), default='organic')
    url = db.Column(db.Text, comment='Конкретный URL')
    title = db.Column(db.Text, comment='Заголовок результата')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'serp_analysis_id': self.serp_analysis_id,
            'competitor_id': self.competitor_id,
            'position': self.position,
            'result_type': self.result_type,
            'url': self.url,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CampaignSite(db.Model):
    """Домены наших сайтов (для кампаний)"""
    __tablename__ = 'campaign_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), unique=True, nullable=False)
    site_url = db.Column(db.String(500))
    domain = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'campaign_id': self.campaign_id,
            'site_url': self.site_url,
            'domain': self.domain,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }