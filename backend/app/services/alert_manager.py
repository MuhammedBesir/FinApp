"""
Alert Manager Service
Trading alert sistemi - price, score, signal alerts
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
from app.utils.logger import logger


class AlertManager:
    """Trading alert yönetimi"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # In-memory storage (production'da Redis veya DB kullan)
        self.alerts: Dict[str, Dict[str, Any]] = {}
        self.triggered_alerts: List[Dict[str, Any]] = []
        self.notification_history: List[Dict[str, Any]] = []  # Bildirim geçmişi
        self.max_history = 100  # Maksimum kayıt sayısı
        self._initialized = True
        logger.info("AlertManager initialized")
    
    def create_alert(
        self,
        alert_type: str,
        ticker: str,
        condition: Dict[str, Any],
        notification: Dict[str, bool] = None,
        priority: str = 'medium'
    ) -> str:
        """
        Yeni alert oluştur
        
        Args:
            alert_type: 'price', 'score', 'signal', 'position'
            ticker: Hisse sembolü
            condition: Alert koşulu (örn: {'price_above': 450.0})
            notification: Bildirim ayarları
        
        Returns:
            Alert ID
        """
        alert_id = str(uuid.uuid4())
        
        if notification is None:
            notification = {
                'browser': True,
                'sound': True
            }
        
        alert = {
            'id': alert_id,
            'type': alert_type,
            'ticker': ticker,
            'condition': condition,
            'triggered': False,
            'active': True,
            'priority': priority,  # low, medium, high, critical
            'created_at': datetime.now().isoformat(),
            'notification': notification,
            'message': self._generate_message(alert_type, ticker, condition)
        }
        
        self.alerts[alert_id] = alert
        logger.info(f"Created alert {alert_id}: {alert_type} for {ticker}")
        
        return alert_id
    
    def _generate_message(self, alert_type: str, ticker: str, condition: Dict) -> str:
        """Alert mesajı oluştur"""
        # IPO bildirimi özel formatı
        if condition.get('type') == 'new_ipo':
            return f"🎉 Yeni Halka Arz: {ticker}"
        
        if alert_type == 'price':
            if 'price_above' in condition:
                return f"{ticker} {condition['price_above']}₺'ye ulaştı! 📈"
            elif 'price_below' in condition:
                return f"{ticker} {condition['price_below']}₺'ye düştü! 📉"
        
        elif alert_type == 'score':
            if 'score_above' in condition:
                return f"{ticker} momentum skoru {condition['score_above']}'ın üstünde! 🎯"
        
        elif alert_type == 'signal':
            return f"{ticker} için BUY sinyali geldi! 💰"
        
        elif alert_type == 'position':
            if 'stop_loss' in condition:
                return f"{ticker} stop-loss tetiklendi! 🛑"
            elif 'take_profit' in condition:
                return f"{ticker} take-profit hedefine ulaştı! ✅"
        
        return f"{ticker} alert tetiklendi"
    
    def check_alert(
        self,
        alert_id: str,
        current_data: Dict[str, Any]
    ) -> bool:
        """
        Bir alert'in tetiklenip tetiklenmediğini kontrol et
        
        Args:
            alert_id: Alert ID
            current_data: Mevcut market data (price, score, vb.)
        
        Returns:
            True if triggered
        """
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        
        if not alert['active'] or alert['triggered']:
            return False
        
        condition = alert['condition']
        alert_type = alert['type']
        
        # Price alerts
        if alert_type == 'price':
            current_price = current_data.get('price', 0)
            
            if 'price_above' in condition:
                if current_price >= condition['price_above']:
                    return self._trigger_alert(alert_id)
            
            elif 'price_below' in condition:
                if current_price <= condition['price_below']:
                    return self._trigger_alert(alert_id)
        
        # Score alerts
        elif alert_type == 'score':
            current_score = current_data.get('score', 0)
            
            if 'score_above' in condition:
                if current_score >= condition['score_above']:
                    return self._trigger_alert(alert_id)
            
            elif 'score_below' in condition:
                if current_score <= condition['score_below']:
                    return self._trigger_alert(alert_id)
        
        # Signal alerts
        elif alert_type == 'signal':
            recommendation = current_data.get('recommendation', '')
            
            if recommendation == 'BUY':
                return self._trigger_alert(alert_id)
        
        return False
    
    def _trigger_alert(self, alert_id: str) -> bool:
        """Alert'i tetikle"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert['triggered'] = True
            alert['triggered_at'] = datetime.now().isoformat()
            
            # Triggered list'e ekle
            self.triggered_alerts.append(alert.copy())
            
            # Geçmişe ekle
            self._add_to_history(alert.copy())
            
            logger.info(f"Alert triggered: {alert_id} - {alert['message']}")
            return True
        
        return False
    
    def check_all_alerts(
        self,
        market_data: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Tüm aktif alertleri kontrol et
        
        Args:
            market_data: {'THYAO.IS': {'price': 450, 'score': 85, ...}, ...}
        
        Returns:
            Tetiklenen alertler
        """
        newly_triggered = []
        
        for alert_id, alert in self.alerts.items():
            if not alert['active'] or alert['triggered']:
                continue
            
            ticker = alert['ticker']
            
            if ticker in market_data:
                if self.check_alert(alert_id, market_data[ticker]):
                    newly_triggered.append(alert)
        
        return newly_triggered
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Aktif alertleri getir"""
        return [
            alert for alert in self.alerts.values()
            if alert['active'] and not alert['triggered']
        ]
    
    def get_triggered_alerts(self, clear: bool = False) -> List[Dict[str, Any]]:
        """
        Tetiklenmiş alertleri getir
        
        Args:
            clear: True ise triggered list'i temizle
        """
        triggered = self.triggered_alerts.copy()
        
        if clear:
            self.triggered_alerts.clear()
        
        return triggered
    
    def delete_alert(self, alert_id: str) -> bool:
        """Alert sil"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            logger.info(f"Deleted alert {alert_id}")
            return True
        
        return False
    
    def toggle_alert(self, alert_id: str, active: bool) -> bool:
        """Alert'i aktif/pasif yap"""
        if alert_id in self.alerts:
            self.alerts[alert_id]['active'] = active
            logger.info(f"Alert {alert_id} set to {'active' if active else 'inactive'}")
            return True
        
        return False
    
    def _add_to_history(self, alert: Dict[str, Any]) -> None:
        """Bildirim geçmişine ekle"""
        self.notification_history.insert(0, {
            **alert,
            'read': False,
            'archived': False
        })
        
        # Maksimum limiti aş, eski kayıtları temizle
        if len(self.notification_history) > self.max_history:
            self.notification_history = self.notification_history[:self.max_history]
    
    def get_notification_history(
        self,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Bildirim geçmişini getir"""
        history = self.notification_history
        
        if unread_only:
            history = [n for n in history if not n.get('read', False)]
        
        return history[:limit]
    
    def mark_notification_read(self, alert_id: str) -> bool:
        """Bildirimi okundu olarak işaretle"""
        for notif in self.notification_history:
            if notif['id'] == alert_id:
                notif['read'] = True
                return True
        return False
    
    def mark_all_read(self) -> int:
        """Tüm bildirimleri okundu işaretle"""
        count = 0
        for notif in self.notification_history:
            if not notif.get('read', False):
                notif['read'] = True
                count += 1
        return count
    
    def clear_history(self, days: int = None) -> int:
        """Bildirim geçmişini temizle"""
        if days is None:
            # Tümünü temizle
            count = len(self.notification_history)
            self.notification_history.clear()
            return count
        else:
            # Belirli gün öncesi kayıtları temizle
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=days)
            
            original_count = len(self.notification_history)
            self.notification_history = [
                n for n in self.notification_history
                if datetime.fromisoformat(n['created_at']) > cutoff
            ]
            return original_count - len(self.notification_history)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Bildirim istatistiklerini getir"""
        total_alerts = len(self.alerts)
        active_alerts = len(self.get_active_alerts())
        triggered_today = len([
            n for n in self.notification_history
            if datetime.fromisoformat(n['created_at']).date() == datetime.now().date()
        ])
        unread_count = len([
            n for n in self.notification_history
            if not n.get('read', False)
        ])
        
        # Türe göre dağılım
        type_distribution = {}
        for alert in self.alerts.values():
            alert_type = alert['type']
            type_distribution[alert_type] = type_distribution.get(alert_type, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_alerts,
            'triggered_today': triggered_today,
            'unread_count': unread_count,
            'total_history': len(self.notification_history),
            'type_distribution': type_distribution
        }
