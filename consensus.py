"""
Модуль консенсуса RAFT
"""
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime
import time
import threading
import random


class NodeState(Enum):
    FOLLOWER = "Follower"
    CANDIDATE = "Candidate"
    LEADER = "Leader"


class RaftNode:
    """Узел консенсуса RAFT"""
    
    def __init__(self, node_id: str, is_central_bank: bool = False):
        self.node_id = node_id
        self.is_central_bank = is_central_bank
        self.state = NodeState.FOLLOWER
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.log: List[Dict] = []
        self.commit_index = -1
        self.last_applied = -1
        self.leader_id: Optional[str] = None
        self.election_timeout = random.uniform(1.5, 3.0)  # секунды
        self.last_heartbeat = time.time()
        self.votes_received = 0
        self.other_nodes: List['RaftNode'] = []
        self.transaction_hashes: List[str] = []
        self.blocks_formed: List[Dict] = []
        self.block_formation_times: List[float] = []
    
    def start_election(self):
        """Начало выборов лидера"""
        if self.is_central_bank:
            # ЦБ всегда лидер
            self.state = NodeState.LEADER
            self.current_term += 1
            self.leader_id = self.node_id
            return True
        
        self.state = NodeState.CANDIDATE
        self.current_term += 1
        self.voted_for = self.node_id
        self.votes_received = 1  # Голос за себя
        
        # Запрос голосов у других узлов
        for node in self.other_nodes:
            if node.state != NodeState.LEADER:
                # Упрощенная логика: если узел не лидер, он голосует
                if node.voted_for is None or node.voted_for == self.node_id:
                    self.votes_received += 1
        
        # Если получили большинство голосов (включая ЦБ)
        total_nodes = len(self.other_nodes) + 1
        if self.votes_received > total_nodes / 2:
            self.state = NodeState.LEADER
            self.leader_id = self.node_id
            return True
        
        return False
    
    def receive_heartbeat(self, leader_id: str, term: int):
        """Получение heartbeat от лидера"""
        if term >= self.current_term:
            self.current_term = term
            self.state = NodeState.FOLLOWER
            self.leader_id = leader_id
            self.last_heartbeat = time.time()
            self.voted_for = None
    
    def append_transaction_hash(self, tx_hash: str):
        """Добавление хеша транзакции"""
        self.transaction_hashes.append({
            'hash': tx_hash,
            'timestamp': datetime.now(),
            'term': self.current_term
        })
    
    def form_block(self, transactions: List, previous_hash: str) -> Optional[Dict]:
        """Формирование блока"""
        if self.state != NodeState.LEADER:
            return None
        
        start_time = time.time()
        
        # Сбор транзакций в блок
        block_data = {
            'block_id': f"BLOCK_{len(self.blocks_formed) + 1}",
            'previous_hash': previous_hash,
            'transactions': transactions,
            'timestamp': datetime.now(),
            'term': self.current_term,
            'node_id': self.node_id
        }
        
        # Распространение блока для подтверждения
        confirmations = 1  # Лидер подтверждает сам
        for node in self.other_nodes:
            if node.state == NodeState.FOLLOWER:
                confirmations += 1
        
        # Если получили большинство подтверждений
        total_nodes = len(self.other_nodes) + 1
        if confirmations > total_nodes / 2:
            formation_time = (time.time() - start_time) * 1000  # в миллисекундах
            block_data['formation_time'] = formation_time
            block_data['confirmations'] = confirmations
            
            self.blocks_formed.append(block_data)
            self.block_formation_times.append(formation_time)
            
            # Распространение блока на все узлы
            for node in self.other_nodes:
                node.receive_block(block_data)
            
            return block_data
        
        return None
    
    def receive_block(self, block_data: Dict):
        """Получение блока от лидера"""
        self.log.append(block_data)
        self.commit_index = len(self.log) - 1


class RaftConsensus:
    """Система консенсуса RAFT"""
    
    def __init__(self, central_bank_id: str, bank_ids: List[str]):
        self.nodes: Dict[str, RaftNode] = {}
        self.central_bank_id = central_bank_id
        
        # Создание узла ЦБ (всегда лидер)
        cb_node = RaftNode(central_bank_id, is_central_bank=True)
        cb_node.state = NodeState.LEADER
        cb_node.leader_id = central_bank_id
        self.nodes[central_bank_id] = cb_node
        
        # Создание узлов ФО
        for bank_id in bank_ids:
            node = RaftNode(bank_id, is_central_bank=False)
            node.other_nodes = [cb_node] + [n for n in self.nodes.values() if not n.is_central_bank]
            cb_node.other_nodes.append(node)
            self.nodes[bank_id] = node
        
        # Обновление связей между узлами
        for node in self.nodes.values():
            if not node.is_central_bank:
                node.other_nodes = [n for n in self.nodes.values() if n.node_id != node.node_id]
    
    def add_transaction_hash(self, tx_hash: str):
        """Добавление хеша транзакции в консенсус"""
        leader = self.get_leader()
        if leader:
            leader.append_transaction_hash(tx_hash)
    
    def get_leader(self) -> Optional[RaftNode]:
        """Получение лидера"""
        for node in self.nodes.values():
            if node.state == NodeState.LEADER:
                return node
        return None
    
    def form_block(self, transactions: List, previous_hash: str) -> Optional[Dict]:
        """Формирование блока через консенсус"""
        leader = self.get_leader()
        if leader:
            return leader.form_block(transactions, previous_hash)
        return None
    
    def get_node_status(self) -> Dict[str, Dict]:
        """Получение статуса всех узлов"""
        status = {}
        for node_id, node in self.nodes.items():
            status[node_id] = {
                'state': node.state.value,
                'term': node.current_term,
                'is_leader': node.state == NodeState.LEADER,
                'transaction_hashes_count': len(node.transaction_hashes),
                'blocks_formed_count': len(node.blocks_formed)
            }
        return status
    
    def get_consensus_metrics(self) -> Dict:
        """Получение метрик консенсуса"""
        leader = self.get_leader()
        if not leader:
            return {}
        
        return {
            'total_transaction_hashes': len(leader.transaction_hashes),
            'total_blocks_formed': len(leader.blocks_formed),
            'avg_block_formation_time': sum(leader.block_formation_times) / len(leader.block_formation_times) if leader.block_formation_times else 0,
            'current_term': leader.current_term,
            'leader_id': leader.node_id
        }

