"""
Модуль работы с базой данных
"""
from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import json

Base = declarative_base()


class UserDB(Base):
    """Таблица пользователей в БД"""
    __tablename__ = 'users'
    
    user_id = Column(String, primary_key=True)
    user_type = Column(String)
    bank_id = Column(String)
    non_cash_balance = Column(Float, default=10000.0)
    digital_wallet_status = Column(String, default='ЗАКРЫТ')
    digital_wallet_balance = Column(Float, default=0.0)
    offline_wallet_status = Column(String, default='ЗАКРЫТ')
    offline_wallet_balance = Column(Float, default=0.0)
    offline_wallet_activation_time = Column(DateTime, nullable=True)
    offline_wallet_deactivation_time = Column(DateTime, nullable=True)


class TransactionDB(Base):
    """Таблица транзакций в БД"""
    __tablename__ = 'transactions'
    
    transaction_id = Column(String, primary_key=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    amount = Column(Float)
    transaction_type = Column(String)
    status = Column(String)
    timestamp = Column(DateTime)
    bank_id = Column(String)
    block_hash = Column(String, nullable=True)
    signature = Column(String, nullable=True)


class OfflineTransactionDB(Base):
    """Таблица офлайн транзакций в БД"""
    __tablename__ = 'offline_transactions'
    
    transaction_id = Column(String, primary_key=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime)
    bank_id = Column(String)
    status = Column(String)
    sync_timestamp = Column(DateTime, nullable=True)


class SmartContractDB(Base):
    """Таблица смарт-контрактов в БД"""
    __tablename__ = 'smart_contracts'
    
    contract_id = Column(String, primary_key=True)
    sender_id = Column(String)
    receiver_id = Column(String)
    amount = Column(Float)
    contract_type = Column(String)
    execution_time = Column(DateTime)
    bank_id = Column(String)
    status = Column(String)
    executed = Column(Boolean, default=False)


class BlockDB(Base):
    """Таблица блоков в БД"""
    __tablename__ = 'blocks'
    
    block_id = Column(String, primary_key=True)
    previous_hash = Column(String)
    transactions_data = Column(Text)  # JSON строка
    timestamp = Column(DateTime)
    merkle_root = Column(String)
    block_hash = Column(String)
    signatures = Column(Text)  # JSON строка
    node_id = Column(String, nullable=True)


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self, db_path: str = 'digital_ruble.db'):
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """Получение сессии БД"""
        return self.Session()
    
    def save_user(self, user):
        """Сохранение пользователя"""
        session = self.get_session()
        try:
            user_db = UserDB(
                user_id=user.user_id,
                user_type=user.user_type.value,
                bank_id=user.bank_id,
                non_cash_balance=user.non_cash_balance,
                digital_wallet_status=user.digital_wallet_status.value,
                digital_wallet_balance=user.digital_wallet_balance,
                offline_wallet_status=user.offline_wallet_status.value,
                offline_wallet_balance=user.offline_wallet_balance,
                offline_wallet_activation_time=user.offline_wallet_activation_time,
                offline_wallet_deactivation_time=user.offline_wallet_deactivation_time
            )
            session.merge(user_db)
            session.commit()
        finally:
            session.close()
    
    def save_transaction(self, transaction):
        """Сохранение транзакции"""
        session = self.get_session()
        try:
            tx_db = TransactionDB(
                transaction_id=transaction.transaction_id,
                sender_id=transaction.sender_id,
                receiver_id=transaction.receiver_id,
                amount=transaction.amount,
                transaction_type=transaction.transaction_type.value,
                status=transaction.status.value,
                timestamp=transaction.timestamp,
                bank_id=transaction.bank_id,
                block_hash=transaction.block_hash,
                signature=transaction.signature
            )
            session.merge(tx_db)
            session.commit()
        finally:
            session.close()
    
    def save_offline_transaction(self, offline_tx):
        """Сохранение офлайн транзакции"""
        session = self.get_session()
        try:
            otx_db = OfflineTransactionDB(
                transaction_id=offline_tx.transaction_id,
                sender_id=offline_tx.sender_id,
                receiver_id=offline_tx.receiver_id,
                amount=offline_tx.amount,
                timestamp=offline_tx.timestamp,
                bank_id=offline_tx.bank_id,
                status=offline_tx.status.value,
                sync_timestamp=offline_tx.sync_timestamp
            )
            session.merge(otx_db)
            session.commit()
        finally:
            session.close()
    
    def save_smart_contract(self, contract):
        """Сохранение смарт-контракта"""
        session = self.get_session()
        try:
            sc_db = SmartContractDB(
                contract_id=contract.contract_id,
                sender_id=contract.sender_id,
                receiver_id=contract.receiver_id,
                amount=contract.amount,
                contract_type=contract.contract_type.value,
                execution_time=contract.execution_time,
                bank_id=contract.bank_id,
                status=contract.status.value,
                executed=contract.executed
            )
            session.merge(sc_db)
            session.commit()
        finally:
            session.close()
    
    def save_block(self, block):
        """Сохранение блока"""
        session = self.get_session()
        try:
            block_db = BlockDB(
                block_id=block.block_id,
                previous_hash=block.previous_hash,
                transactions_data=json.dumps([tx.to_dict() for tx in block.transactions]),
                timestamp=block.timestamp,
                merkle_root=block.merkle_root,
                block_hash=block.block_hash,
                signatures=json.dumps(block.signatures),
                node_id=block.node_id
            )
            session.merge(block_db)
            session.commit()
        finally:
            session.close()
    
    def get_all_users(self):
        """Получение всех пользователей"""
        session = self.get_session()
        try:
            return session.query(UserDB).all()
        finally:
            session.close()
    
    def get_all_transactions(self):
        """Получение всех транзакций"""
        session = self.get_session()
        try:
            return session.query(TransactionDB).all()
        finally:
            session.close()
    
    def get_all_offline_transactions(self):
        """Получение всех офлайн транзакций"""
        session = self.get_session()
        try:
            return session.query(OfflineTransactionDB).all()
        finally:
            session.close()
    
    def get_all_smart_contracts(self):
        """Получение всех смарт-контрактов"""
        session = self.get_session()
        try:
            return session.query(SmartContractDB).all()
        finally:
            session.close()
    
    def get_all_blocks(self):
        """Получение всех блоков"""
        session = self.get_session()
        try:
            return session.query(BlockDB).order_by(BlockDB.timestamp).all()
        finally:
            session.close()

