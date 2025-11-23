"""
Модуль обработки транзакций
"""
from models import Transaction, OfflineTransaction, SmartContract, TransactionType, TransactionStatus, SmartContractType
from participants import UserManager, FinancialOrganization
from crypto import CryptoService
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import uuid
import time


class TransactionProcessor:
    """Процессор транзакций"""
    
    def __init__(self, user_manager: UserManager, database):
        self.user_manager = user_manager
        self.database = database
        self.transactions: List[Transaction] = []
        self.offline_transactions: List[OfflineTransaction] = []
        self.smart_contracts: List[SmartContract] = []
        self.pending_transactions: List[Transaction] = []
        self.metrics = {'tx_creation_times': []}
    
    def create_online_transaction(self, sender_id: str, receiver_id: str, amount: float) -> Optional[Transaction]:
        """Создание онлайн транзакции"""
        start_time = time.time()
        
        sender = self.user_manager.get_user(sender_id)
        receiver = self.user_manager.get_user(receiver_id)
        
        if not sender or not receiver:
            return None
        
        bank = self.user_manager.get_bank(sender.bank_id) if sender.bank_id else None
        if not bank:
            return None
        
        # Валидация
        if not bank.validate_transaction(sender, amount):
            return None
        
        # Создание транзакции
        tx_id = f"TX_{uuid.uuid4().hex[:12]}"
        transaction = Transaction(
            transaction_id=tx_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            transaction_type=TransactionType.ONLINE,
            status=TransactionStatus.PENDING,
            timestamp=datetime.now(),
            bank_id=sender.bank_id
        )
        
        # Подписание транзакции
        tx_data = f"{tx_id}{sender_id}{receiver_id}{amount}"
        transaction.signature = CryptoService.sign_data(tx_data, bank.private_key)
        
        # Выполнение транзакции
        sender.digital_wallet_balance -= amount
        receiver.digital_wallet_balance += amount
        transaction.status = TransactionStatus.CONFIRMED
        
        self.transactions.append(transaction)
        self.pending_transactions.append(transaction)
        self.database.save_transaction(transaction)
        
        # Обновление метрик
        creation_time = (time.time() - start_time) * 1000  # в миллисекундах
        self.metrics['tx_creation_times'].append(creation_time)
        
        return transaction
    
    def create_offline_transaction(self, sender_id: str, receiver_id: str, amount: float) -> Optional[OfflineTransaction]:
        """Создание офлайн транзакции"""
        sender = self.user_manager.get_user(sender_id)
        receiver = self.user_manager.get_user(receiver_id)
        
        if not sender or not receiver:
            return None
        
        if sender.offline_wallet_status.value != "ОТКРЫТ":
            return None
        
        if sender.offline_wallet_balance < amount:
            return None
        
        tx_id = f"OTX_{uuid.uuid4().hex[:12]}"
        offline_tx = OfflineTransaction(
            transaction_id=tx_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            timestamp=datetime.now(),
            bank_id=sender.bank_id,
            status=TransactionStatus.OFFLINE
        )
        
        # Выполнение офлайн транзакции
        sender.offline_wallet_balance -= amount
        receiver.offline_wallet_balance += amount
        
        self.offline_transactions.append(offline_tx)
        self.database.save_offline_transaction(offline_tx)
        
        return offline_tx
    
    def sync_offline_transactions(self):
        """Синхронизация офлайн транзакций"""
        for offline_tx in self.offline_transactions:
            if offline_tx.status == TransactionStatus.OFFLINE:
                offline_tx.status = TransactionStatus.IN_PROCESSING
                offline_tx.sync_timestamp = datetime.now()
                
                # Проверка на двойную трату - проверяем, что средства уже были списаны при создании
                sender = self.user_manager.get_user(offline_tx.sender_id)
                receiver = self.user_manager.get_user(offline_tx.receiver_id)
                
                # Проверяем, что транзакция не была выполнена дважды
                duplicate = False
                for existing_tx in self.transactions:
                    if (existing_tx.transaction_id == offline_tx.transaction_id or
                        (existing_tx.sender_id == offline_tx.sender_id and
                         existing_tx.receiver_id == offline_tx.receiver_id and
                         existing_tx.amount == offline_tx.amount and
                         abs((existing_tx.timestamp - offline_tx.timestamp).total_seconds()) < 60)):
                        duplicate = True
                        break
                
                if not duplicate and sender and receiver:
                    # Конвертация в обычную транзакцию
                    transaction = Transaction(
                        transaction_id=offline_tx.transaction_id,
                        sender_id=offline_tx.sender_id,
                        receiver_id=offline_tx.receiver_id,
                        amount=offline_tx.amount,
                        transaction_type=TransactionType.OFFLINE,
                        status=TransactionStatus.CONFIRMED,
                        timestamp=offline_tx.sync_timestamp,
                        bank_id=offline_tx.bank_id
                    )
                    offline_tx.status = TransactionStatus.PROCESSED
                    self.transactions.append(transaction)
                    self.pending_transactions.append(transaction)
                    self.database.save_transaction(transaction)
                else:
                    offline_tx.status = TransactionStatus.REJECTED
                    # Возврат средств при отклонении
                    if sender:
                        sender.offline_wallet_balance += offline_tx.amount
                    if receiver:
                        receiver.offline_wallet_balance -= offline_tx.amount
                
                self.database.save_offline_transaction(offline_tx)
    
    def create_smart_contract(self, sender_id: str, receiver_id: str, amount: float, 
                             contract_type: SmartContractType, execution_delay_hours: int = 0) -> Optional[SmartContract]:
        """Создание смарт-контракта"""
        sender = self.user_manager.get_user(sender_id)
        receiver = self.user_manager.get_user(receiver_id)
        
        if not sender or not receiver:
            return None
        
        bank = self.user_manager.get_bank(sender.bank_id) if sender.bank_id else None
        if not bank:
            return None
        
        if sender.digital_wallet_balance < amount:
            return None
        
        contract_id = f"SC_{uuid.uuid4().hex[:12]}"
        execution_time = datetime.now() + timedelta(hours=execution_delay_hours)
        
        contract = SmartContract(
            contract_id=contract_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            amount=amount,
            contract_type=contract_type,
            execution_time=execution_time,
            bank_id=sender.bank_id,
            status=TransactionStatus.PENDING
        )
        
        # Резервирование средств
        sender.digital_wallet_balance -= amount
        
        self.smart_contracts.append(contract)
        self.database.save_smart_contract(contract)
        
        return contract
    
    def execute_smart_contract(self, contract: SmartContract) -> bool:
        """Исполнение смарт-контракта"""
        if contract.executed:
            return False
        
        if datetime.now() < contract.execution_time:
            return False
        
        sender = self.user_manager.get_user(contract.sender_id)
        receiver = self.user_manager.get_user(contract.receiver_id)
        
        if not sender or not receiver:
            return False
        
        # Средства уже зарезервированы при создании, просто переводим получателю
        receiver.digital_wallet_balance += contract.amount
        
        # Создание транзакции из смарт-контракта
        transaction = Transaction(
            transaction_id=contract.contract_id,
            sender_id=contract.sender_id,
            receiver_id=contract.receiver_id,
            amount=contract.amount,
            transaction_type=TransactionType.SMART_CONTRACT,
            status=TransactionStatus.CONFIRMED,
            timestamp=datetime.now(),
            bank_id=contract.bank_id
        )
        
        contract.executed = True
        contract.status = TransactionStatus.CONFIRMED
        self.transactions.append(transaction)
        self.pending_transactions.append(transaction)
        
        self.database.save_smart_contract(contract)
        self.database.save_transaction(transaction)
        
        return True
    
    def get_pending_transactions(self) -> List[Transaction]:
        """Получение ожидающих транзакций"""
        return self.pending_transactions.copy()
    
    def clear_pending_transactions(self):
        """Очистка обработанных транзакций"""
        self.pending_transactions = []

