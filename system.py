"""
Основной модуль системы цифрового рубля
"""
from participants import UserManager, CentralBank, FinancialOrganization
from transactions import TransactionProcessor
from consensus import RaftConsensus
from blockchain import Blockchain
from database import DatabaseManager
from models import UserType, SmartContractType, TransactionType
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading
import time
import random
import uuid


class DigitalRubleSystem:
    """Основная система цифрового рубля"""
    
    def __init__(self):
        self.database = DatabaseManager()
        self.user_manager = UserManager()
        self.transaction_processor: Optional[TransactionProcessor] = None
        self.consensus: Optional[RaftConsensus] = None
        self.blockchain: Optional[Blockchain] = None
        self.central_bank: Optional[CentralBank] = None
        self.simulation_running = False
        self.simulation_thread: Optional[threading.Thread] = None
        self.callbacks = {}  # Callbacks для обновления GUI
    
    def initialize_system(self):
        """Инициализация системы"""
        # Создание ЦБ
        self.central_bank = self.user_manager.create_central_bank()
        self.database.save_user(self.central_bank.user)
        
        # Инициализация процессора транзакций
        self.transaction_processor = TransactionProcessor(self.user_manager, self.database)
    
    def create_banks(self, count: int) -> List[str]:
        """Создание банков"""
        bank_ids = []
        for i in range(count):
            bank_id = f"BANK_{i+1}"
            bank = self.user_manager.create_bank(bank_id)
            self.database.save_user(bank.user)
            bank_ids.append(bank_id)
        return bank_ids
    
    def create_users(self, count: int, user_type: UserType) -> List[str]:
        """Создание пользователей"""
        user_ids = []
        banks = list(self.user_manager.banks.keys())
        
        if not banks:
            return user_ids
        
        for i in range(count):
            bank_id = random.choice(banks)
            user = self.user_manager.create_user(user_type, bank_id)
            self.database.save_user(user)
            user_ids.append(user.user_id)
        
        return user_ids
    
    def setup_consensus_and_blockchain(self):
        """Настройка консенсуса и блокчейна"""
        bank_ids = list(self.user_manager.banks.keys())
        self.consensus = RaftConsensus(self.central_bank.bank_id, bank_ids)
        self.blockchain = Blockchain(
            self.consensus,
            self.central_bank,
            self.user_manager.banks
        )
        self.blockchain.create_genesis_block()
    
    def start_simulation(self, scenario: int = 1):
        """Запуск симуляции"""
        if self.simulation_running:
            return
        
        self.simulation_running = True
        self.simulation_thread = threading.Thread(
            target=self._run_simulation,
            args=(scenario,),
            daemon=True
        )
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Остановка симуляции"""
        self.simulation_running = False
    
    def _run_simulation(self, scenario: int):
        """Выполнение симуляции"""
        scenarios = {
            1: {'users': 1000, 'banks': 5, 'duration_minutes': 2, 'tx_per_minute': 2075},
            2: {'users': 10000, 'banks': 10, 'duration_minutes': 2, 'tx_per_minute': 20900},
            3: {'users': 50000, 'banks': 15, 'duration_minutes': 2, 'tx_per_minute': 104250}
        }
        
        config = scenarios.get(scenario, scenarios[1])
        
        # Создание пользователей и банков если их нет
        if not self.user_manager.banks:
            self.create_banks(config['banks'])
        
        if len(self.user_manager.users) < config['users']:
            needed = config['users'] - len(self.user_manager.users)
            self.create_users(needed // 2, UserType.INDIVIDUAL)
            self.create_users(needed // 2, UserType.LEGAL)
        
        # Настройка консенсуса и блокчейна
        if not self.consensus:
            self.setup_consensus_and_blockchain()
        
        # Симуляция процессов
        start_time = time.time()
        end_time = start_time + (config['duration_minutes'] * 60)
        tx_count = 0
        target_tx = config['tx_per_minute'] * config['duration_minutes']
        
        users = [u for u in self.user_manager.get_all_users() 
                if u.user_type in [UserType.INDIVIDUAL, UserType.LEGAL]]
        
        while self.simulation_running and time.time() < end_time and tx_count < target_tx:
            # Создание цифровых кошельков
            for user in random.sample(users, min(10, len(users))):
                if user.digital_wallet_status.value == "ЗАКРЫТ":
                    bank = self.user_manager.get_bank(user.bank_id)
                    if bank:
                        bank.create_wallet(user)
                        bank.top_up_digital_wallet(user, random.uniform(100, 1000))
                        self.database.save_user(user)
                        self._notify_callback('user_updated', user)
            
            # Создание офлайн кошельков
            for user in random.sample(users, min(5, len(users))):
                if user.digital_wallet_status.value == "ОТКРЫТ" and user.offline_wallet_status.value == "ЗАКРЫТ":
                    bank = self.user_manager.get_bank(user.bank_id)
                    if bank and user.digital_wallet_balance > 0:
                        bank.create_offline_wallet(user)
                        amount = min(random.uniform(50, 200), user.digital_wallet_balance)
                        bank.top_up_offline_wallet(user, amount)
                        self.database.save_user(user)
                        self._notify_callback('user_updated', user)
            
            # Создание онлайн транзакций
            for _ in range(min(20, target_tx - tx_count)):
                if not users:
                    break
                sender = random.choice(users)
                receiver = random.choice([u for u in users if u.user_id != sender.user_id])
                
                if sender.digital_wallet_balance > 0:
                    amount = min(random.uniform(10, 500), sender.digital_wallet_balance)
                    tx = self.transaction_processor.create_online_transaction(
                        sender.user_id, receiver.user_id, amount
                    )
                    if tx:
                        tx_count += 1
                        self._notify_callback('transaction_created', tx)
                        
                        # Добавление хеша в консенсус
                        tx_hash = tx.calculate_hash()
                        self.consensus.add_transaction_hash(tx_hash)
            
            # Создание офлайн транзакций
            offline_users = [u for u in users if u.offline_wallet_status.value == "ОТКРЫТ" and u.offline_wallet_balance > 0]
            for _ in range(min(5, len(offline_users))):
                if len(offline_users) < 2:
                    break
                sender = random.choice(offline_users)
                receiver = random.choice([u for u in offline_users if u.user_id != sender.user_id])
                
                amount = min(random.uniform(10, 100), sender.offline_wallet_balance)
                otx = self.transaction_processor.create_offline_transaction(
                    sender.user_id, receiver.user_id, amount
                )
                if otx:
                    self._notify_callback('offline_transaction_created', otx)
            
            # Создание смарт-контрактов
            for _ in range(min(3, len(users))):
                sender = random.choice(users)
                receiver = random.choice([u for u in users if u.user_id != sender.user_id])
                
                if sender.digital_wallet_balance > 100:
                    contract_type = random.choice(list(SmartContractType))
                    amount = min(random.uniform(100, 1000), sender.digital_wallet_balance)
                    contract = self.transaction_processor.create_smart_contract(
                        sender.user_id, receiver.user_id, amount, contract_type, 0
                    )
                    if contract:
                        self._notify_callback('smart_contract_created', contract)
            
            # Синхронизация офлайн транзакций
            self.transaction_processor.sync_offline_transactions()
            
            # Формирование блока
            pending_txs = self.transaction_processor.get_pending_transactions()
            if len(pending_txs) >= 10:  # Формируем блок каждые 10 транзакций
                block = self.blockchain.add_block(pending_txs[:10])
                if block:
                    self._notify_callback('block_created', block)
                    self.transaction_processor.clear_pending_transactions()
            
            # Исполнение смарт-контрактов
            for contract in self.transaction_processor.smart_contracts:
                if not contract.executed:
                    self.transaction_processor.execute_smart_contract(contract)
            
            time.sleep(0.1)  # Небольшая задержка
        
        self.simulation_running = False
    
    def _notify_callback(self, event: str, data):
        """Уведомление callback"""
        if event in self.callbacks:
            try:
                self.callbacks[event](data)
            except:
                pass
    
    def register_callback(self, event: str, callback):
        """Регистрация callback"""
        self.callbacks[event] = callback
    
    def get_metrics(self) -> Dict:
        """Получение метрик системы"""
        if not self.transaction_processor or not self.blockchain:
            return {}
        
        tx_metrics = self.transaction_processor.metrics
        blockchain_metrics = self.blockchain.metrics
        consensus_metrics = self.consensus.get_consensus_metrics() if self.consensus else {}
        
        total_tx = len(self.transaction_processor.transactions)
        avg_tx_time = sum(tx_metrics.get('tx_creation_times', [])) / len(tx_metrics.get('tx_creation_times', [1])) if tx_metrics.get('tx_creation_times') else 0
        avg_block_time = sum(blockchain_metrics.get('block_creation_times', [])) / len(blockchain_metrics.get('block_creation_times', [1])) if blockchain_metrics.get('block_creation_times') else 0
        avg_registry_time = sum(blockchain_metrics.get('block_registry_times', [])) / len(blockchain_metrics.get('block_registry_times', [1])) if blockchain_metrics.get('block_registry_times') else 0
        
        return {
            'total_transactions': total_tx,
            'avg_transaction_time': avg_tx_time,
            'avg_block_creation_time': avg_block_time,
            'avg_block_registry_time': avg_registry_time,
            'system_load': total_tx / 1000.0 if total_tx > 0 else 0,
            'tps': total_tx / 120.0 if total_tx > 0 else 0,  # За 2 минуты
            **consensus_metrics
        }

