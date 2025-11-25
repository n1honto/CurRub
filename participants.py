"""
Модуль участников системы
"""
from models import User, UserType, WalletStatus
from crypto import CryptoService
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid


class CentralBank:
    """Центральный банк России"""
    
    def __init__(self):
        self.bank_id = "CB_RF"
        self.private_key, self.public_key = CryptoService.generate_key_pair()
        self.total_emission = 0.0
        self.emission_requests: List[Dict] = []
        self.user = User(
            user_id=self.bank_id,
            user_type=UserType.CENTRAL_BANK,
            non_cash_balance=0.0
        )
    
    def process_emission_request(self, bank_id: str, amount: float) -> bool:
        """Обработка запроса на эмиссию"""
        # Условия для одобрения эмиссии
        if amount > 0 and amount <= 1000000:  # Максимальная сумма эмиссии
            self.total_emission += amount
            return True
        return False
    
    def sign_block(self, block_data: str) -> str:
        """Подписание блока электронной подписью"""
        return CryptoService.sign_data(block_data, self.private_key)


class FinancialOrganization:
    """Финансовая организация (банк)"""
    
    def __init__(self, bank_id: str):
        self.bank_id = bank_id
        self.private_key, self.public_key = CryptoService.generate_key_pair()
        self.clients: Dict[str, User] = {}
        self.transactions: List = []
        self.user = User(
            user_id=self.bank_id,
            user_type=UserType.BANK,
            non_cash_balance=0.0
        )
    
    def create_wallet(self, user: User) -> bool:
        """Создание цифрового кошелька для клиента"""
        if user.digital_wallet_status == WalletStatus.CLOSED:
            user.digital_wallet_status = WalletStatus.OPEN
            return True
        return False
    
    def top_up_digital_wallet(self, user: User, amount: float, transaction_processor=None) -> bool:
        """Пополнение цифрового кошелька"""
        if user.digital_wallet_status != WalletStatus.OPEN:
            return False
        if user.non_cash_balance < amount:
            return False
        
        user.non_cash_balance -= amount
        user.digital_wallet_balance += amount
        
        # Создание транзакции пополнения
        if transaction_processor:
            from models import Transaction, TransactionType, TransactionStatus
            import uuid
            tx_id = f"TOPUP_{uuid.uuid4().hex[:12]}"
            topup_tx = Transaction(
                transaction_id=tx_id,
                sender_id=user.user_id,  # Отправитель - сам пользователь
                receiver_id=user.user_id,  # Получатель - сам пользователь
                amount=amount,
                transaction_type=TransactionType.WALLET_TOPUP,
                status=TransactionStatus.CONFIRMED,
                timestamp=datetime.now(),
                bank_id=user.bank_id or self.bank_id
            )
            transaction_processor.transactions.append(topup_tx)
            transaction_processor.pending_transactions.append(topup_tx)
            transaction_processor.database.save_transaction(topup_tx)
        
        return True
    
    def withdraw_from_digital_wallet(self, user: User, amount: float) -> bool:
        """Вывод средств с цифрового кошелька"""
        if user.digital_wallet_status != WalletStatus.OPEN:
            return False
        if user.digital_wallet_balance < amount:
            return False
        
        user.digital_wallet_balance -= amount
        user.non_cash_balance += amount
        return True
    
    def create_offline_wallet(self, user: User) -> bool:
        """Создание офлайн кошелька"""
        if user.offline_wallet_status == WalletStatus.CLOSED:
            user.offline_wallet_status = WalletStatus.OPEN
            user.offline_wallet_activation_time = datetime.now()
            user.offline_wallet_deactivation_time = datetime.now() + timedelta(days=14)
            return True
        return False
    
    def top_up_offline_wallet(self, user: User, amount: float, transaction_processor=None) -> bool:
        """Пополнение офлайн кошелька"""
        if user.offline_wallet_status != WalletStatus.OPEN:
            return False
        if user.digital_wallet_balance < amount:
            return False
        if datetime.now() > user.offline_wallet_deactivation_time:
            user.offline_wallet_status = WalletStatus.CLOSED
            return False
        
        user.digital_wallet_balance -= amount
        user.offline_wallet_balance += amount
        
        # Создание транзакции пополнения офлайн кошелька
        if transaction_processor:
            from models import Transaction, TransactionType, TransactionStatus
            import uuid
            tx_id = f"OTOPUP_{uuid.uuid4().hex[:12]}"
            topup_tx = Transaction(
                transaction_id=tx_id,
                sender_id=user.user_id,
                receiver_id=user.user_id,
                amount=amount,
                transaction_type=TransactionType.OFFLINE_WALLET_TOPUP,
                status=TransactionStatus.CONFIRMED,
                timestamp=datetime.now(),
                bank_id=user.bank_id or self.bank_id
            )
            transaction_processor.transactions.append(topup_tx)
            transaction_processor.pending_transactions.append(topup_tx)
            transaction_processor.database.save_transaction(topup_tx)
        
        return True
    
    def validate_transaction(self, sender: User, amount: float) -> bool:
        """Валидация транзакции"""
        if sender.digital_wallet_balance < amount:
            return False
        return True
    
    def sign_block(self, block_data: str) -> str:
        """Подписание блока электронной подписью"""
        return CryptoService.sign_data(block_data, self.private_key)
    
    def request_emission(self, amount: float) -> Dict:
        """Запрос на эмиссию к ЦБ"""
        return {
            'bank_id': self.bank_id,
            'amount': amount,
            'timestamp': datetime.now()
        }


class UserManager:
    """Менеджер пользователей"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.central_bank: Optional[CentralBank] = None
        self.banks: Dict[str, FinancialOrganization] = {}
    
    def create_central_bank(self) -> CentralBank:
        """Создание центрального банка"""
        self.central_bank = CentralBank()
        self.users[self.central_bank.bank_id] = self.central_bank.user
        return self.central_bank
    
    def create_bank(self, bank_id: str) -> FinancialOrganization:
        """Создание финансовой организации"""
        bank = FinancialOrganization(bank_id)
        self.banks[bank_id] = bank
        self.users[bank_id] = bank.user
        return bank
    
    def create_user(self, user_type: UserType, bank_id: Optional[str] = None) -> User:
        """Создание пользователя"""
        user_id = f"USER_{uuid.uuid4().hex[:8]}"
        user = User(
            user_id=user_id,
            user_type=user_type,
            bank_id=bank_id
        )
        self.users[user_id] = user
        
        if bank_id and bank_id in self.banks:
            self.banks[bank_id].clients[user_id] = user
        
        return user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Получение пользователя"""
        return self.users.get(user_id)
    
    def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        return list(self.users.values())
    
    def get_bank(self, bank_id: str) -> Optional[FinancialOrganization]:
        """Получение банка"""
        return self.banks.get(bank_id)

