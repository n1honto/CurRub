"""
Модели данных для системы цифрового рубля
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from dataclasses import dataclass, field
import hashlib
import json


class UserType(Enum):
    INDIVIDUAL = "Физическое лицо"
    LEGAL = "Юридическое лицо"
    BANK = "Финансовая организация"
    CENTRAL_BANK = "Центральный банк"


class WalletStatus(Enum):
    CLOSED = "ЗАКРЫТ"
    OPEN = "ОТКРЫТ"


class TransactionType(Enum):
    ONLINE = "Онлайн транзакция"
    OFFLINE = "Оффлайн транзакция"
    SMART_CONTRACT = "Смарт-контракт"
    WALLET_TOPUP = "Пополнение цифрового кошелька"
    OFFLINE_WALLET_TOPUP = "Пополнение офлайн кошелька"


class TransactionStatus(Enum):
    PENDING = "В обработке"
    CONFIRMED = "Подтверждена"
    REJECTED = "Отклонена"
    OFFLINE = "ОФФЛАЙН"
    IN_PROCESSING = "ПОСТУПИЛО В ОБРАБОТКУ"
    PROCESSED = "ОБРАБОТАНА"


class SmartContractType(Enum):
    UTILITIES = "Оплата коммунальных платежей"
    SUBSCRIPTION = "Оплата подписки"
    AUTOPAYMENT = "Автоплатеж"


@dataclass
class User:
    """Модель пользователя"""
    user_id: str
    user_type: UserType
    bank_id: Optional[str] = None
    non_cash_balance: float = 10000.0
    digital_wallet_status: WalletStatus = WalletStatus.CLOSED
    digital_wallet_balance: float = 0.0
    offline_wallet_status: WalletStatus = WalletStatus.CLOSED
    offline_wallet_balance: float = 0.0
    offline_wallet_activation_time: Optional[datetime] = None
    offline_wallet_deactivation_time: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_type': self.user_type.value,
            'bank_id': self.bank_id,
            'non_cash_balance': self.non_cash_balance,
            'digital_wallet_status': self.digital_wallet_status.value,
            'digital_wallet_balance': self.digital_wallet_balance,
            'offline_wallet_status': self.offline_wallet_status.value,
            'offline_wallet_balance': self.offline_wallet_balance,
            'offline_wallet_activation_time': self.offline_wallet_activation_time.isoformat() if self.offline_wallet_activation_time else None,
            'offline_wallet_deactivation_time': self.offline_wallet_deactivation_time.isoformat() if self.offline_wallet_deactivation_time else None
        }


@dataclass
class Transaction:
    """Модель транзакции"""
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: float
    transaction_type: TransactionType
    status: TransactionStatus
    timestamp: datetime
    bank_id: str
    block_hash: Optional[str] = None
    signature: Optional[str] = None
    
    def calculate_hash(self) -> str:
        """Вычисление хеша транзакции"""
        data = f"{self.transaction_id}{self.sender_id}{self.receiver_id}{self.amount}{self.transaction_type.value}{self.timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type.value,
            'status': self.status.value,
            'timestamp': self.timestamp.isoformat(),
            'bank_id': self.bank_id,
            'block_hash': self.block_hash,
            'signature': self.signature
        }


@dataclass
class OfflineTransaction:
    """Модель офлайн транзакции"""
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: datetime
    bank_id: str
    status: TransactionStatus = TransactionStatus.OFFLINE
    sync_timestamp: Optional[datetime] = None
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'amount': self.amount,
            'timestamp': self.timestamp.isoformat(),
            'bank_id': self.bank_id,
            'status': self.status.value,
            'sync_timestamp': self.sync_timestamp.isoformat() if self.sync_timestamp else None
        }


@dataclass
class SmartContract:
    """Модель смарт-контракта"""
    contract_id: str
    sender_id: str
    receiver_id: str
    amount: float
    contract_type: SmartContractType
    execution_time: datetime
    bank_id: str
    status: TransactionStatus = TransactionStatus.PENDING
    executed: bool = False
    
    def to_dict(self):
        return {
            'contract_id': self.contract_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'amount': self.amount,
            'contract_type': self.contract_type.value,
            'execution_time': self.execution_time.isoformat(),
            'bank_id': self.bank_id,
            'status': self.status.value,
            'executed': self.executed
        }


@dataclass
class Block:
    """Модель блока в блокчейне"""
    block_id: str
    previous_hash: str
    transactions: List[Transaction]
    timestamp: datetime
    merkle_root: str
    block_hash: str
    signatures: List[str] = field(default_factory=list)
    node_id: Optional[str] = None
    
    def calculate_merkle_root(self) -> str:
        """Вычисление корня Меркла"""
        if not self.transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        tx_hashes = [tx.calculate_hash() for tx in self.transactions]
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            tx_hashes = [hashlib.sha256((tx_hashes[i] + tx_hashes[i+1]).encode()).hexdigest() 
                        for i in range(0, len(tx_hashes), 2)]
        return tx_hashes[0]
    
    def calculate_hash(self) -> str:
        """Вычисление хеша блока"""
        data = f"{self.block_id}{self.previous_hash}{self.merkle_root}{self.timestamp.isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def to_dict(self):
        return {
            'block_id': self.block_id,
            'previous_hash': self.previous_hash,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp.isoformat(),
            'merkle_root': self.merkle_root,
            'block_hash': self.block_hash,
            'signatures': self.signatures,
            'node_id': self.node_id
        }


@dataclass
class Metrics:
    """Модель метрик системы"""
    total_transactions: int = 0
    transaction_creation_times: List[float] = field(default_factory=list)
    block_creation_times: List[float] = field(default_factory=list)
    block_registry_times: List[float] = field(default_factory=list)
    system_load: float = 0.0
    tps: float = 0.0
    
    def to_dict(self):
        return {
            'total_transactions': self.total_transactions,
            'avg_transaction_time': sum(self.transaction_creation_times) / len(self.transaction_creation_times) if self.transaction_creation_times else 0,
            'avg_block_creation_time': sum(self.block_creation_times) / len(self.block_creation_times) if self.block_creation_times else 0,
            'avg_registry_time': sum(self.block_registry_times) / len(self.block_registry_times) if self.block_registry_times else 0,
            'system_load': self.system_load,
            'tps': self.tps
        }

