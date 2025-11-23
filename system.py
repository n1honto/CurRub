"""
Основной модуль системы цифрового рубля
"""
from participants import UserManager, CentralBank, FinancialOrganization
from transactions import TransactionProcessor
from consensus import RaftConsensus
from blockchain import Blockchain
from database import DatabaseManager
from models import UserType, SmartContractType, TransactionType
from consensus import NodeState
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
        self.simulation_start_time: Optional[float] = None
        self.simulation_duration: float = 120.0  # секунды
        self.failed_nodes: List[str] = []  # Список отказавших узлов
        self.recovering_nodes: Dict[str, float] = {}  # Узлы в процессе восстановления {node_id: recovery_start_time}
        self.emission_requests: List[Dict] = []  # Запросы на эмиссию
        self.block_formation_events: List[Dict] = []  # События формирования блоков
        self.block_signing_events: List[Dict] = []  # События подписания блоков
        self.incident_recovery_events: List[Dict] = []  # События восстановления после инцидентов
    
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
    
    def start_simulation(self, scenario: int = 1, custom_config: Optional[Dict] = None, incident_config: Optional[Dict] = None):
        """Запуск симуляции"""
        if self.simulation_running:
            return
        
        self.simulation_running = True
        self.simulation_start_time = time.time()
        self.failed_nodes = []
        self.recovering_nodes = {}
        self.emission_requests = []
        self.block_formation_events = []
        self.block_signing_events = []
        self.incident_recovery_events = []
        
        if incident_config:
            self.failed_nodes = incident_config.get('failed_nodes', [])
        
        self.simulation_thread = threading.Thread(
            target=self._run_simulation,
            args=(scenario, custom_config, incident_config),
            daemon=True
        )
        self.simulation_thread.start()
    
    def stop_simulation(self):
        """Остановка симуляции"""
        self.simulation_running = False
    
    def _run_simulation(self, scenario: int, custom_config: Optional[Dict] = None, incident_config: Optional[Dict] = None):
        """Выполнение симуляции"""
        scenarios = {
            1: {'users': 1000, 'banks': 5, 'duration_minutes': 2, 'tx_per_minute': 2075},
            2: {'users': 10000, 'banks': 10, 'duration_minutes': 2, 'tx_per_minute': 20900},
            3: {'users': 50000, 'banks': 15, 'duration_minutes': 2, 'tx_per_minute': 104250}
        }
        
        config = scenarios.get(scenario, scenarios[1])
        if custom_config:
            config.update(custom_config)
        
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
        
        # Применение инцидентов (отказ узлов)
        if incident_config and self.consensus:
            for node_id in self.failed_nodes:
                if node_id in self.consensus.nodes:
                    node = self.consensus.nodes[node_id]
                    node.state = NodeState.FOLLOWER  # Помечаем как недоступный
                    self._notify_callback('node_failed', {'node_id': node_id})
        
        # Симуляция процессов
        start_time = time.time()
        duration_seconds = min(config['duration_minutes'] * 60, 120)  # Максимум 2 минуты
        self.simulation_duration = duration_seconds
        end_time = start_time + duration_seconds
        tx_count = 0
        target_tx = config['tx_per_minute'] * config['duration_minutes']
        last_emission_time = start_time
        emission_interval = 30  # Запросы на эмиссию каждые 30 секунд
        last_incident_tx_count = 0
        incident_tx_interval = random.randint(700, 1200)  # Инциденты каждые 700-1200 транзакций
        incident_count = 0
        max_incidents = 10  # Максимум инцидентов за симуляцию
        
        users = [u for u in self.user_manager.get_all_users() 
                if u.user_type in [UserType.INDIVIDUAL, UserType.LEGAL]]
        
        while self.simulation_running:
            current_time = time.time()
            
            # Строгая проверка времени - не более 2 минут
            elapsed = current_time - start_time
            if elapsed >= duration_seconds:
                break
            
            # Проверка количества транзакций
            if tx_count >= target_tx:
                break
            
            # Обработка восстановления узлов
            self._process_node_recovery(current_time)
            
            # Симуляция запросов на эмиссию от банков
            if current_time - last_emission_time >= emission_interval and self.user_manager.banks:
                bank = random.choice(list(self.user_manager.banks.values()))
                amount = random.uniform(50000, 500000)
                request = bank.request_emission(amount)
                self.emission_requests.append({
                    **request,
                    'status': 'pending',
                    'approved': False
                })
                self._notify_callback('emission_request', request)
                last_emission_time = current_time
                
                # Обработка запроса ЦБ
                approved = self.central_bank.process_emission_request(bank.bank_id, amount)
                if approved:
                    self.emission_requests[-1]['status'] = 'approved'
                    self.emission_requests[-1]['approved'] = True
                    self._notify_callback('emission_approved', {'bank_id': bank.bank_id, 'amount': amount})
            
            # Автоматическая симуляция инцидентов (по количеству транзакций)
            # Инцидент "cb_fo_2_failure" исключен из автоматических - только ручной запуск
            if (tx_count - last_incident_tx_count >= incident_tx_interval and 
                incident_count < max_incidents and 
                self.consensus and 
                len(self.user_manager.banks) >= 4):
                incident_types = ['fo_1_failure', 'fo_2_failure']
                if len(self.user_manager.banks) >= 5:
                    incident_types.append('cb_failure')
                
                incident_type = random.choice(incident_types)
                result = self.simulate_incident(incident_type)
                if result.get('success'):
                    incident_count += 1
                    self._notify_callback('incident_handled', result)
                    # Генерируем новый интервал для следующего инцидента
                    incident_tx_interval = random.randint(700, 1200)
                last_incident_tx_count = tx_count
            
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
                # Событие формирования блока
                block_formation_event = {
                    'timestamp': datetime.now(),
                    'pending_transactions': len(pending_txs),
                    'stage': 'block_formation_started'
                }
                self.block_formation_events.append(block_formation_event)
                self._notify_callback('block_formation_started', block_formation_event)
                
                block = self.blockchain.add_block(pending_txs[:10])
                if block:
                    # Событие подписания блока
                    signing_event = {
                        'timestamp': datetime.now(),
                        'block_id': block.block_id,
                        'signatures_count': len(block.signatures),
                        'stage': 'block_signed'
                    }
                    self.block_signing_events.append(signing_event)
                    self._notify_callback('block_signed', signing_event)
                    
                    # Событие записи в реестр
                    registry_event = {
                        'timestamp': datetime.now(),
                        'block_id': block.block_id,
                        'stage': 'block_registered'
                    }
                    self._notify_callback('block_registered', registry_event)
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
    
    def get_simulation_time_remaining(self) -> float:
        """Получение оставшегося времени симуляции"""
        if not self.simulation_start_time or not self.simulation_running:
            return 0.0
        elapsed = time.time() - self.simulation_start_time
        remaining = self.simulation_duration - elapsed
        return max(0.0, remaining)
    
    def get_simulation_elapsed_time(self) -> float:
        """Получение прошедшего времени симуляции"""
        if not self.simulation_start_time:
            return 0.0
        return time.time() - self.simulation_start_time
    
    def _process_node_recovery(self, current_time: float):
        """Обработка восстановления узлов"""
        import time
        recovery_events = []
        
        for node_id, recovery_start in list(self.recovering_nodes.items()):
            # Время восстановления зависит от типа узла
            if node_id == self.central_bank.bank_id:
                recovery_duration = random.uniform(1.5, 2.1)  # 1.8 ± 0.3 с
            else:
                recovery_duration = random.uniform(0.5, 1.5)  # Не менее 0.5 секунды
            
            if current_time - recovery_start >= recovery_duration:
                # Узел восстановлен
                if node_id in self.failed_nodes:
                    self.failed_nodes.remove(node_id)
                if node_id in self.consensus.nodes:
                    node = self.consensus.nodes[node_id]
                    node.state = NodeState.FOLLOWER
                    if node.is_central_bank:
                        node.state = NodeState.LEADER
                        node.leader_id = node_id
                
                recovery_events.append({
                    'node_id': node_id,
                    'timestamp': datetime.now(),
                    'stage': 'node_recovered',
                    'message': f'Узел {node_id} восстановлен и вернулся к работе'
                })
                del self.recovering_nodes[node_id]
        
        for event in recovery_events:
            self.incident_recovery_events.append(event)
            self._notify_callback('node_recovered', event)
    
    def simulate_incident(self, incident_type: str) -> Dict:
        """Симуляция инцидента с поэтапным восстановлением"""
        if not self.consensus:
            return {'success': False, 'message': 'Консенсус не инициализирован'}
        
        import time
        import random
        
        result = {
            'incident_type': incident_type,
            'timestamp': datetime.now(),
            'success': False,
            'quorum_reached': False,
            'recovery_time': 0.0,
            'stages': []
        }
        
        total_nodes = len(self.consensus.nodes)
        active_nodes = [n for n in self.consensus.nodes.values() if n.node_id not in self.failed_nodes]
        
        if incident_type == 'cb_failure':
            # Отказ ЦБ
            if self.central_bank.bank_id not in self.failed_nodes:
                failed_node = self.central_bank.bank_id
                self.failed_nodes.append(failed_node)
                result['stages'].append({
                    'stage': 'node_failed',
                    'message': f'Узел {failed_node} (ЦБ) отказал',
                    'timestamp': datetime.now()
                })
                
                # Выбор нового лидера из ФО
                fo_nodes = [n for n in active_nodes if not n.is_central_bank and n.node_id not in self.failed_nodes]
                if len(fo_nodes) >= 3:  # Кворум
                    new_leader = fo_nodes[0]
                    new_leader.state = NodeState.LEADER
                    new_leader.leader_id = new_leader.node_id
                    result['stages'].append({
                        'stage': 'quorum_check',
                        'message': f'Кворум выполнен ({len(fo_nodes)}/4 ФО активны). Новый лидер: {new_leader.node_id}',
                        'timestamp': datetime.now()
                    })
                    result['stages'].append({
                        'stage': 'work_continues',
                        'message': 'Работа системы продолжается с новым лидером',
                        'timestamp': datetime.now()
                    })
                    result['quorum_reached'] = True
                    recovery_time = random.uniform(1.5, 2.1)  # 1.8 ± 0.3 с
                    result['recovery_time'] = recovery_time
                    self.recovering_nodes[failed_node] = time.time()
                    result['stages'].append({
                        'stage': 'recovery_started',
                        'message': f'Начато восстановление узла {failed_node}. Время восстановления: {recovery_time:.2f} с',
                        'timestamp': datetime.now()
                    })
                    result['success'] = True
                    self._notify_callback('incident_handled', result)
        
        elif incident_type == 'fo_1_failure':
            # Отказ 1 ФО
            fo_nodes = [n for n in self.consensus.nodes.values() if not n.is_central_bank]
            if fo_nodes and fo_nodes[0].node_id not in self.failed_nodes:
                failed_node = fo_nodes[0].node_id
                self.failed_nodes.append(failed_node)
                result['stages'].append({
                    'stage': 'node_failed',
                    'message': f'Узел {failed_node} (ФО) отказал',
                    'timestamp': datetime.now()
                })
                
                active_count = total_nodes - len(self.failed_nodes)
                if active_count > total_nodes / 2:
                    result['stages'].append({
                        'stage': 'quorum_check',
                        'message': f'Кворум выполнен ({active_count}/{total_nodes} узлов активны)',
                        'timestamp': datetime.now()
                    })
                    result['stages'].append({
                        'stage': 'work_continues',
                        'message': 'Работа системы продолжается',
                        'timestamp': datetime.now()
                    })
                    result['quorum_reached'] = True
                    recovery_time = random.uniform(0.5, 1.0)  # Не менее 0.5 секунды
                    result['recovery_time'] = recovery_time
                    self.recovering_nodes[failed_node] = time.time()
                    result['stages'].append({
                        'stage': 'recovery_started',
                        'message': f'Начато восстановление узла {failed_node}. Время восстановления: {recovery_time:.2f} с',
                        'timestamp': datetime.now()
                    })
                    result['success'] = True
                    self._notify_callback('incident_handled', result)
        
        elif incident_type == 'fo_2_failure':
            # Отказ 2 ФО
            fo_nodes = [n for n in self.consensus.nodes.values() if not n.is_central_bank]
            failed_nodes_list = []
            for node in fo_nodes[:2]:
                if node.node_id not in self.failed_nodes:
                    failed_node = node.node_id
                    self.failed_nodes.append(failed_node)
                    failed_nodes_list.append(failed_node)
                    result['stages'].append({
                        'stage': 'node_failed',
                        'message': f'Узел {failed_node} (ФО) отказал',
                        'timestamp': datetime.now()
                    })
            
            active_count = total_nodes - len(self.failed_nodes)
            if active_count > total_nodes / 2:
                result['stages'].append({
                    'stage': 'quorum_check',
                    'message': f'Кворум выполнен ({active_count}/{total_nodes} узлов активны)',
                    'timestamp': datetime.now()
                })
                result['stages'].append({
                    'stage': 'work_continues',
                    'message': 'Работа системы продолжается',
                    'timestamp': datetime.now()
                })
                result['quorum_reached'] = True
                recovery_time = random.uniform(0.5, 1.0)  # Не менее 0.5 секунды
                result['recovery_time'] = recovery_time
                for failed_node in failed_nodes_list:
                    self.recovering_nodes[failed_node] = time.time()
                    result['stages'].append({
                        'stage': 'recovery_started',
                        'message': f'Начато восстановление узла {failed_node}. Время восстановления: {recovery_time:.2f} с',
                        'timestamp': datetime.now()
                    })
                result['success'] = True
                self._notify_callback('incident_handled', result)
        
        elif incident_type == 'cb_fo_2_failure':
            # Отказ ЦБ + 2 ФО
            failed_nodes_list = []
            if self.central_bank.bank_id not in self.failed_nodes:
                failed_node = self.central_bank.bank_id
                self.failed_nodes.append(failed_node)
                failed_nodes_list.append(failed_node)
                result['stages'].append({
                    'stage': 'node_failed',
                    'message': f'Узел {failed_node} (ЦБ) отказал',
                    'timestamp': datetime.now()
                })
            
            fo_nodes = [n for n in self.consensus.nodes.values() if not n.is_central_bank]
            for node in fo_nodes[:2]:
                if node.node_id not in self.failed_nodes:
                    failed_node = node.node_id
                    self.failed_nodes.append(failed_node)
                    failed_nodes_list.append(failed_node)
                    result['stages'].append({
                        'stage': 'node_failed',
                        'message': f'Узел {failed_node} (ФО) отказал',
                        'timestamp': datetime.now()
                    })
            
            active_count = total_nodes - len(self.failed_nodes)
            if active_count <= total_nodes / 2:
                result['stages'].append({
                    'stage': 'quorum_failed',
                    'message': f'Кворум не достигнут ({active_count}/{total_nodes} узлов активны)',
                    'timestamp': datetime.now()
                })
                result['quorum_reached'] = False
                result['success'] = True
                result['message'] = 'Аварийная остановка'
                self._notify_callback('incident_handled', result)
        
        return result

