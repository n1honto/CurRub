"""
Модуль распределенного реестра (блокчейна)
"""
from models import Block, Transaction
from crypto import CryptoService
from consensus import RaftConsensus
from participants import CentralBank, FinancialOrganization
from database import DatabaseManager
from datetime import datetime
from typing import List, Dict, Optional
import hashlib
import time


class Blockchain:
    """Распределенный реестр (блокчейн)"""
    
    def __init__(self, consensus: RaftConsensus, central_bank: CentralBank,
                 banks: Dict[str, FinancialOrganization], database: DatabaseManager):
        self.chain: List[Block] = []
        self.consensus = consensus
        self.central_bank = central_bank
        self.banks = banks
        self.nodes: Dict[str, List[Block]] = {}  # Распределение блоков по узлам
        self.genesis_block_created = False
        self.metrics = {'block_creation_times': [], 'block_registry_times': []}
        self.database = database
    
    def create_genesis_block(self):
        """Создание генезис-блока"""
        if self.genesis_block_created:
            return
        
        genesis_block = Block(
            block_id="GENESIS",
            previous_hash="0" * 64,
            transactions=[],
            timestamp=datetime.now(),
            merkle_root="0" * 64,
            block_hash="",
            node_id=self.central_bank.bank_id
        )
        
        genesis_block.merkle_root = genesis_block.calculate_merkle_root()
        genesis_block.block_hash = genesis_block.calculate_hash()
        
        # Подписание блока ЦБ
        block_data = f"{genesis_block.block_id}{genesis_block.block_hash}"
        signature = self.central_bank.sign_block(block_data)
        genesis_block.signatures.append(signature)
        
        self.chain.append(genesis_block)
        self.database.save_block(genesis_block)
        self._distribute_block(genesis_block)
        self.genesis_block_created = True
    
    def add_block(self, transactions: List[Transaction]) -> Optional[Block]:
        """Добавление нового блока"""
        if not transactions:
            return None
        
        start_time = time.time()
        
        # Получение предыдущего блока
        previous_block = self.chain[-1] if self.chain else None
        previous_hash = previous_block.block_hash if previous_block else "0" * 64
        
        # Формирование блока через консенсус
        block_data = self.consensus.form_block(
            [tx.to_dict() for tx in transactions],
            previous_hash
        )
        
        if not block_data:
            return None
        
        # Создание блока
        block_id = block_data['block_id']
        block = Block(
            block_id=block_id,
            previous_hash=previous_hash,
            transactions=transactions,
            timestamp=block_data['timestamp'],
            merkle_root="",
            block_hash="",
            node_id=block_data.get('node_id')
        )
        
        # Вычисление корня Меркла
        block.merkle_root = block.calculate_merkle_root()
        
        # Вычисление хеша блока
        block.block_hash = block.calculate_hash()
        
        # Подписание блока ЦБ
        block_data_str = f"{block.block_id}{block.block_hash}"
        cb_signature = self.central_bank.sign_block(block_data_str)
        block.signatures.append(cb_signature)
        
        # Подписание блока ФО
        for bank_id, bank in self.banks.items():
            bank_signature = bank.sign_block(block_data_str)
            block.signatures.append(bank_signature)
        
        # Запись в реестр
        registry_start = time.time()
        self.chain.append(block)
        self.database.save_block(block)
        self._distribute_block(block)
        
        # Обновление метрик
        creation_time = (time.time() - start_time) * 1000
        registry_time = (time.time() - registry_start) * 1000
        self.metrics['block_creation_times'].append(creation_time)
        self.metrics['block_registry_times'].append(registry_time)
        
        # Обновление транзакций с хешем блока
        for tx in transactions:
            tx.block_hash = block.block_hash
            self.database.save_transaction(tx)
        
        return block
    
    def _distribute_block(self, block: Block):
        """Распределение блока по узлам"""
        # ЦБ получает все блоки
        if self.central_bank.bank_id not in self.nodes:
            self.nodes[self.central_bank.bank_id] = []
        self.nodes[self.central_bank.bank_id].append(block)
        self.database.save_block_registry_event(
            block.block_id,
            self.central_bank.bank_id,
            status="registered",
            details="Блок записан в реестр ЦБ"
        )
        
        # Распределение по ФО (каждый получает копию)
        for bank_id in self.banks.keys():
            if bank_id not in self.nodes:
                self.nodes[bank_id] = []
            self.nodes[bank_id].append(block)
            self.database.save_block_registry_event(
                block.block_id,
                bank_id,
                status="replicated",
                details="Блок реплицирован в узел ФО"
            )
    
    def verify_chain(self) -> bool:
        """Проверка целостности цепочки"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Проверка связи с предыдущим блоком
            if current_block.previous_hash != previous_block.block_hash:
                return False
            
            # Проверка хеша текущего блока
            calculated_hash = current_block.calculate_hash()
            if calculated_hash != current_block.block_hash:
                return False
        
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Block]:
        """Получение блока по хешу"""
        for block in self.chain:
            if block.block_hash == block_hash:
                return block
        return None
    
    def get_transaction_history(self, wallet_id: str) -> List[Transaction]:
        """Получение истории транзакций для кошелька"""
        transactions = []
        for block in self.chain:
            for tx in block.transactions:
                if tx.sender_id == wallet_id or tx.receiver_id == wallet_id:
                    transactions.append(tx)
        return transactions
    
    def get_chain_info(self) -> Dict:
        """Получение информации о цепочке"""
        return {
            'total_blocks': len(self.chain),
            'chain_valid': self.verify_chain(),
            'nodes_count': len(self.nodes),
            'blocks_per_node': {node_id: len(blocks) for node_id, blocks in self.nodes.items()}
        }

