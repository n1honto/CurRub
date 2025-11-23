"""
GUI приложение для системы цифрового рубля
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from system import DigitalRubleSystem
from models import UserType, SmartContractType, TransactionType, WalletStatus
from participants import FinancialOrganization
from datetime import datetime
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import json


class DigitalRubleGUI:
    """Графический интерфейс системы цифрового рубля"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Платформа цифрового рубля - Имитационная модель")
        self.root.geometry("1400x900")
        
        self.system = DigitalRubleSystem()
        self.system.initialize_system()
        
        # Регистрация callbacks
        self.system.register_callback('user_updated', self.on_user_updated)
        self.system.register_callback('transaction_created', self.on_transaction_created)
        self.system.register_callback('offline_transaction_created', self.on_offline_transaction_created)
        self.system.register_callback('smart_contract_created', self.on_smart_contract_created)
        self.system.register_callback('block_created', self.on_block_created)
        
        # Создание вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_management_tab()
        self.create_user_tab()
        self.create_bank_tab()
        self.create_central_bank_tab()
        self.create_users_data_tab()
        self.create_transactions_data_tab()
        self.create_offline_transactions_tab()
        self.create_smart_contracts_tab()
        self.create_consensus_tab()
        self.create_blockchain_tab()
        self.create_metrics_tab()
        
        # Таймер обновления
        self.update_timer()
    
    def create_management_tab(self):
        """Вкладка 1: Управление"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Управление")
        
        # Создание пользователей
        ttk.Label(frame, text="Создание пользователей", font=("Arial", 12, "bold")).pack(pady=10)
        
        user_frame = ttk.Frame(frame)
        user_frame.pack(pady=5)
        
        ttk.Label(user_frame, text="Количество:").grid(row=0, column=0, padx=5)
        self.user_count_var = tk.StringVar(value="10")
        ttk.Entry(user_frame, textvariable=self.user_count_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Label(user_frame, text="Тип:").grid(row=0, column=2, padx=5)
        self.user_type_var = tk.StringVar(value="Физическое лицо")
        user_type_combo = ttk.Combobox(user_frame, textvariable=self.user_type_var, 
                                      values=["Физическое лицо", "Юридическое лицо"], 
                                      state="readonly", width=20)
        user_type_combo.grid(row=0, column=3, padx=5)
        
        ttk.Button(user_frame, text="Создать пользователей", 
                  command=self.create_users_manual).grid(row=0, column=4, padx=5)
        
        # Создание банков
        ttk.Label(frame, text="Создание банков (ФО)", font=("Arial", 12, "bold")).pack(pady=10)
        
        bank_frame = ttk.Frame(frame)
        bank_frame.pack(pady=5)
        
        ttk.Label(bank_frame, text="Количество:").grid(row=0, column=0, padx=5)
        self.bank_count_var = tk.StringVar(value="5")
        ttk.Entry(bank_frame, textvariable=self.bank_count_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Button(bank_frame, text="Создать банки", 
                  command=self.create_banks_manual).grid(row=0, column=2, padx=5)
        
        # Симуляция
        ttk.Label(frame, text="Симуляция", font=("Arial", 12, "bold")).pack(pady=20)
        
        sim_frame = ttk.Frame(frame)
        sim_frame.pack(pady=5)
        
        ttk.Label(sim_frame, text="Сценарий:").grid(row=0, column=0, padx=5)
        self.scenario_var = tk.StringVar(value="1")
        scenario_combo = ttk.Combobox(sim_frame, textvariable=self.scenario_var,
                                     values=["1 - Низкая нагрузка", "2 - Средняя нагрузка", "3 - Пиковая нагрузка"],
                                     state="readonly", width=25)
        scenario_combo.grid(row=0, column=1, padx=5)
        
        self.sim_button = ttk.Button(sim_frame, text="Запустить симуляцию", 
                                     command=self.start_simulation)
        self.sim_button.grid(row=0, column=2, padx=5)
        
        ttk.Button(sim_frame, text="Остановить симуляцию", 
                  command=self.stop_simulation).grid(row=0, column=3, padx=5)
        
        # Статус
        self.status_label = ttk.Label(frame, text="Статус: Готов к работе", 
                                     font=("Arial", 10))
        self.status_label.pack(pady=20)
    
    def create_user_tab(self):
        """Вкладка 2: Пользователь"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Пользователь")
        
        # Выбор пользователя
        user_select_frame = ttk.Frame(frame)
        user_select_frame.pack(pady=10)
        
        ttk.Label(user_select_frame, text="Пользователь:").pack(side=tk.LEFT, padx=5)
        self.user_select_var = tk.StringVar()
        self.user_select_combo = ttk.Combobox(user_select_frame, textvariable=self.user_select_var,
                                              state="readonly", width=30)
        self.user_select_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(user_select_frame, text="Обновить список", 
                  command=self.update_user_list).pack(side=tk.LEFT, padx=5)
        
        # Функции пользователя
        func_frame = ttk.LabelFrame(frame, text="Функции пользователя")
        func_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Создание цифрового кошелька
        ttk.Button(func_frame, text="Создать цифровой кошелек", 
                  command=self.create_digital_wallet).pack(pady=5)
        
        # Пополнение цифрового кошелька
        topup_frame = ttk.Frame(func_frame)
        topup_frame.pack(pady=5)
        ttk.Label(topup_frame, text="Сумма:").pack(side=tk.LEFT, padx=5)
        self.topup_amount_var = tk.StringVar(value="1000")
        ttk.Entry(topup_frame, textvariable=self.topup_amount_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(topup_frame, text="Пополнить цифровой кошелек", 
                  command=self.topup_digital_wallet).pack(side=tk.LEFT, padx=5)
        
        # Создание онлайн транзакции
        tx_frame = ttk.LabelFrame(func_frame, text="Онлайн транзакция")
        tx_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Label(tx_frame, text="Получатель:").grid(row=0, column=0, padx=5, pady=5)
        self.tx_receiver_var = tk.StringVar()
        self.tx_receiver_combo = ttk.Combobox(tx_frame, textvariable=self.tx_receiver_var, width=25, state="readonly")
        self.tx_receiver_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(tx_frame, text="Сумма:").grid(row=1, column=0, padx=5, pady=5)
        self.tx_amount_var = tk.StringVar(value="100")
        ttk.Entry(tx_frame, textvariable=self.tx_amount_var, width=15).grid(row=1, column=1, padx=5)
        
        ttk.Button(tx_frame, text="Создать транзакцию", 
                  command=self.create_user_transaction).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Офлайн кошелек
        offline_frame = ttk.LabelFrame(func_frame, text="Офлайн кошелек")
        offline_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Button(offline_frame, text="Открыть офлайн кошелек", 
                  command=self.create_offline_wallet).pack(pady=5)
        
        ttk.Label(offline_frame, text="Сумма пополнения:").pack(pady=5)
        self.offline_topup_var = tk.StringVar(value="200")
        ttk.Entry(offline_frame, textvariable=self.offline_topup_var, width=15).pack(pady=5)
        ttk.Button(offline_frame, text="Пополнить офлайн кошелек", 
                  command=self.topup_offline_wallet).pack(pady=5)
        
        # Офлайн транзакция
        ttk.Label(offline_frame, text="Получатель:").pack(pady=5)
        self.offline_receiver_var = tk.StringVar()
        self.offline_receiver_combo = ttk.Combobox(offline_frame, textvariable=self.offline_receiver_var, width=25, state="readonly")
        self.offline_receiver_combo.pack(pady=5)
        
        ttk.Label(offline_frame, text="Сумма:").pack(pady=5)
        self.offline_tx_amount_var = tk.StringVar(value="50")
        ttk.Entry(offline_frame, textvariable=self.offline_tx_amount_var, width=15).pack(pady=5)
        ttk.Button(offline_frame, text="Создать офлайн транзакцию", 
                  command=self.create_offline_transaction).pack(pady=5)
        
        # Смарт-контракт
        sc_frame = ttk.LabelFrame(func_frame, text="Смарт-контракт")
        sc_frame.pack(pady=5, fill=tk.X, padx=10)
        
        ttk.Label(sc_frame, text="Тип:").grid(row=0, column=0, padx=5, pady=5)
        self.sc_type_var = tk.StringVar(value="Оплата коммунальных платежей")
        sc_type_combo = ttk.Combobox(sc_frame, textvariable=self.sc_type_var,
                                    values=["Оплата коммунальных платежей", "Оплата подписки", "Автоплатеж"],
                                    state="readonly", width=25)
        sc_type_combo.grid(row=0, column=1, padx=5)
        
        ttk.Label(sc_frame, text="Получатель:").grid(row=1, column=0, padx=5, pady=5)
        self.sc_receiver_var = tk.StringVar()
        self.sc_receiver_combo = ttk.Combobox(sc_frame, textvariable=self.sc_receiver_var, width=25, state="readonly")
        self.sc_receiver_combo.grid(row=1, column=1, padx=5)
        
        ttk.Label(sc_frame, text="Сумма:").grid(row=2, column=0, padx=5, pady=5)
        self.sc_amount_var = tk.StringVar(value="1000")
        ttk.Entry(sc_frame, textvariable=self.sc_amount_var, width=15).grid(row=2, column=1, padx=5)
        
        ttk.Button(sc_frame, text="Создать смарт-контракт", 
                  command=self.create_smart_contract).grid(row=3, column=0, columnspan=2, pady=5)
    
    def create_bank_tab(self):
        """Вкладка 3: Финансовая организация"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Финансовая организация")
        
        # Выбор банка
        bank_select_frame = ttk.Frame(frame)
        bank_select_frame.pack(pady=10)
        
        ttk.Label(bank_select_frame, text="Банк:").pack(side=tk.LEFT, padx=5)
        self.bank_select_var = tk.StringVar()
        self.bank_select_combo = ttk.Combobox(bank_select_frame, textvariable=self.bank_select_var,
                                              state="readonly", width=30)
        self.bank_select_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(bank_select_frame, text="Обновить список", 
                  command=self.update_bank_list).pack(side=tk.LEFT, padx=5)
        
        # Запрос на эмиссию
        emission_frame = ttk.LabelFrame(frame, text="Запрос на эмиссию")
        emission_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(emission_frame, text="Сумма эмиссии:").grid(row=0, column=0, padx=5, pady=5)
        self.emission_amount_var = tk.StringVar(value="100000")
        ttk.Entry(emission_frame, textvariable=self.emission_amount_var, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(emission_frame, text="Отправить запрос", 
                  command=self.request_emission).grid(row=0, column=2, padx=5)
        
        # Транзакции банка
        tx_frame = ttk.LabelFrame(frame, text="Транзакции банка")
        tx_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Таблица транзакций
        columns = ("ID", "Отправитель", "Получатель", "Сумма", "Тип", "Время")
        self.bank_tx_tree = ttk.Treeview(tx_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.bank_tx_tree.heading(col, text=col)
            self.bank_tx_tree.column(col, width=120)
        self.bank_tx_tree.pack(fill=tk.BOTH, expand=True)
        
        # Уведомления
        notif_frame = ttk.LabelFrame(frame, text="Уведомления")
        notif_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.bank_notifications = scrolledtext.ScrolledText(notif_frame, height=10, wrap=tk.WORD)
        self.bank_notifications.pack(fill=tk.BOTH, expand=True)
    
    def create_central_bank_tab(self):
        """Вкладка 4: Центральный банк"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Центральный банк")
        
        # Запросы на эмиссию
        emission_frame = ttk.LabelFrame(frame, text="Запросы на эмиссию")
        emission_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Банк", "Сумма", "Время", "Статус")
        self.cb_emission_tree = ttk.Treeview(emission_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.cb_emission_tree.heading(col, text=col)
            self.cb_emission_tree.column(col, width=150)
        self.cb_emission_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        action_frame = ttk.Frame(emission_frame)
        action_frame.pack(pady=5)
        
        ttk.Button(action_frame, text="Одобрить выбранный", 
                  command=self.approve_emission).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Отклонить выбранный", 
                  command=self.reject_emission).pack(side=tk.LEFT, padx=5)
        
        # Контроль системы
        control_frame = ttk.LabelFrame(frame, text="Контроль системы")
        control_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        info_text = scrolledtext.ScrolledText(control_frame, height=15, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.cb_info_text = info_text
        
        ttk.Button(control_frame, text="Обновить информацию", 
                  command=self.update_cb_info).pack(pady=5)
    
    def create_users_data_tab(self):
        """Вкладка 5: Данные о пользователях"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Данные о пользователях")
        
        # Таблица пользователей
        columns = ("ID", "Тип", "Безнал. баланс", "Цифр. кошелек", "Цифр. баланс", 
                  "Офлайн кошелек", "Офлайн баланс", "Активация офлайн", "Деактивация офлайн")
        self.users_tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)
        
        for col in columns:
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=scrollbar.set)
        
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(frame, text="Обновить данные", 
                  command=self.update_users_table).pack(pady=5)
    
    def create_transactions_data_tab(self):
        """Вкладка 6: Данные о транзакциях"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Данные о транзакциях")
        
        columns = ("Отправитель", "Получатель", "Тип", "Сумма", "Время", "Банк")
        self.transactions_tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)
        
        for col in columns:
            self.transactions_tree.heading(col, text=col)
            self.transactions_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
        self.transactions_tree.configure(yscrollcommand=scrollbar.set)
        
        self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(frame, text="Обновить данные", 
                  command=self.update_transactions_table).pack(pady=5)
    
    def create_offline_transactions_tab(self):
        """Вкладка 7: Оффлайн-транзакции"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Оффлайн-транзакции")
        
        columns = ("Отправитель", "Получатель", "Сумма", "Банк", "Время", "Состояние")
        self.offline_tx_tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)
        
        for col in columns:
            self.offline_tx_tree.heading(col, text=col)
            self.offline_tx_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.offline_tx_tree.yview)
        self.offline_tx_tree.configure(yscrollcommand=scrollbar.set)
        
        self.offline_tx_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(frame, text="Обновить данные", 
                  command=self.update_offline_transactions_table).pack(pady=5)
    
    def create_smart_contracts_tab(self):
        """Вкладка 8: Смарт-контракты"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Смарт-контракты")
        
        columns = ("Отправитель", "Получатель", "Сумма", "Банк", "Тип", "Время исполнения", "Статус")
        self.smart_contracts_tree = ttk.Treeview(frame, columns=columns, show="headings", height=25)
        
        for col in columns:
            self.smart_contracts_tree.heading(col, text=col)
            self.smart_contracts_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.smart_contracts_tree.yview)
        self.smart_contracts_tree.configure(yscrollcommand=scrollbar.set)
        
        self.smart_contracts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(frame, text="Обновить данные", 
                  command=self.update_smart_contracts_table).pack(pady=5)
    
    def create_consensus_tab(self):
        """Вкладка 9: Консенсус"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Консенсус")
        
        # Визуализация консенсуса
        viz_frame = ttk.LabelFrame(frame, text="Визуализация RAFT консенсуса")
        viz_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.consensus_canvas = tk.Canvas(viz_frame, bg="white", height=400)
        self.consensus_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Таблица хешей транзакций
        hash_frame = ttk.LabelFrame(frame, text="Хеши транзакций")
        hash_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Хеш", "Время", "Терм")
        self.tx_hash_tree = ttk.Treeview(hash_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tx_hash_tree.heading(col, text=col)
            self.tx_hash_tree.column(col, width=200)
        self.tx_hash_tree.pack(fill=tk.BOTH, expand=True)
        
        # Таблица блоков
        block_frame = ttk.LabelFrame(frame, text="Сформированные блоки")
        block_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID блока", "Время формирования", "Кол-во транзакций", "Подтверждения")
        self.consensus_blocks_tree = ttk.Treeview(block_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.consensus_blocks_tree.heading(col, text=col)
            self.consensus_blocks_tree.column(col, width=150)
        self.consensus_blocks_tree.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(frame, text="Обновить визуализацию", 
                  command=self.update_consensus_visualization).pack(pady=5)
    
    def create_blockchain_tab(self):
        """Вкладка 10: Распределенный реестр"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Распределенный реестр")
        
        # Визуализация блокчейна
        viz_frame = ttk.LabelFrame(frame, text="Визуализация блокчейна")
        viz_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.blockchain_canvas = tk.Canvas(viz_frame, bg="white", height=500)
        self.blockchain_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Информация о блоках
        info_frame = ttk.LabelFrame(frame, text="Информация о блоках")
        info_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Предыдущий хеш", "Хеш блока", "Время", "Узел", "Транзакций")
        self.blocks_tree = ttk.Treeview(info_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.blocks_tree.heading(col, text=col)
            self.blocks_tree.column(col, width=150)
        self.blocks_tree.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(frame, text="Обновить визуализацию", 
                  command=self.update_blockchain_visualization).pack(pady=5)
    
    def create_metrics_tab(self):
        """Вкладка 11: Анализ метрик"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Анализ метрик")
        
        # Графики
        graph_frame = ttk.LabelFrame(frame, text="Графики метрик")
        graph_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.metrics_figure = plt.Figure(figsize=(12, 8), dpi=100)
        self.metrics_canvas = FigureCanvasTkAgg(self.metrics_figure, graph_frame)
        self.metrics_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Таблица метрик
        table_frame = ttk.LabelFrame(frame, text="Метрики системы")
        table_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Метрика", "Значение")
        self.metrics_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.metrics_tree.heading(col, text=col)
            self.metrics_tree.column(col, width=200)
        self.metrics_tree.pack(fill=tk.BOTH, expand=True)
        
        ttk.Button(frame, text="Обновить метрики", 
                  command=self.update_metrics).pack(pady=5)
    
    # Методы обработки событий
    def create_users_manual(self):
        try:
            count = int(self.user_count_var.get())
            user_type_str = self.user_type_var.get()
            user_type = UserType.INDIVIDUAL if user_type_str == "Физическое лицо" else UserType.LEGAL
            
            user_ids = self.system.create_users(count, user_type)
            messagebox.showinfo("Успех", f"Создано пользователей: {len(user_ids)}")
            self.update_user_list()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def create_banks_manual(self):
        try:
            count = int(self.bank_count_var.get())
            bank_ids = self.system.create_banks(count)
            if not self.system.consensus:
                self.system.setup_consensus_and_blockchain()
            messagebox.showinfo("Успех", f"Создано банков: {len(bank_ids)}")
            self.update_bank_list()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def start_simulation(self):
        try:
            scenario = int(self.scenario_var.get().split()[0])
            self.system.start_simulation(scenario)
            self.status_label.config(text="Статус: Симуляция запущена")
            self.sim_button.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def stop_simulation(self):
        self.system.stop_simulation()
        self.status_label.config(text="Статус: Симуляция остановлена")
        self.sim_button.config(state="normal")
    
    def update_user_list(self):
        users = self.system.user_manager.get_all_users()
        user_list = [f"{u.user_id} ({u.user_type.value})" for u in users 
                    if u.user_type in [UserType.INDIVIDUAL, UserType.LEGAL]]
        self.user_select_combo['values'] = user_list
        if user_list and not self.user_select_var.get():
            self.user_select_combo.current(0)
        
        # Обновление списков получателей
        if hasattr(self, 'tx_receiver_combo'):
            self.tx_receiver_combo['values'] = user_list
        if hasattr(self, 'offline_receiver_combo'):
            self.offline_receiver_combo['values'] = user_list
        if hasattr(self, 'sc_receiver_combo'):
            self.sc_receiver_combo['values'] = user_list
    
    def update_bank_list(self):
        banks = list(self.system.user_manager.banks.keys())
        self.bank_select_combo['values'] = banks
        if banks:
            self.bank_select_combo.current(0)
    
    def create_digital_wallet(self):
        user_id = self.user_select_var.get().split()[0]
        user = self.system.user_manager.get_user(user_id)
        if user:
            bank = self.system.user_manager.get_bank(user.bank_id)
            if bank:
                if bank.create_wallet(user):
                    self.system.database.save_user(user)
                    messagebox.showinfo("Успех", "Цифровой кошелек создан")
                else:
                    messagebox.showwarning("Предупреждение", "Кошелек уже открыт")
    
    def topup_digital_wallet(self):
        user_id = self.user_select_var.get().split()[0]
        amount = float(self.topup_amount_var.get())
        user = self.system.user_manager.get_user(user_id)
        if user:
            bank = self.system.user_manager.get_bank(user.bank_id)
            if bank:
                if bank.top_up_digital_wallet(user, amount):
                    self.system.database.save_user(user)
                    messagebox.showinfo("Успех", f"Кошелек пополнен на {amount} ЦР")
                else:
                    messagebox.showerror("Ошибка", "Недостаточно средств или кошелек закрыт")
    
    def create_user_transaction(self):
        sender_id = self.user_select_var.get().split()[0]
        receiver_id = self.tx_receiver_var.get().split()[0] if self.tx_receiver_var.get() else None
        amount = float(self.tx_amount_var.get())
        
        if not receiver_id:
            messagebox.showerror("Ошибка", "Выберите получателя")
            return
        
        tx = self.system.transaction_processor.create_online_transaction(sender_id, receiver_id, amount)
        if tx:
            messagebox.showinfo("Успех", "Транзакция создана")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать транзакцию")
    
    def create_offline_wallet(self):
        user_id = self.user_select_var.get().split()[0]
        user = self.system.user_manager.get_user(user_id)
        if user:
            bank = self.system.user_manager.get_bank(user.bank_id)
            if bank:
                if bank.create_offline_wallet(user):
                    self.system.database.save_user(user)
                    messagebox.showinfo("Успех", "Офлайн кошелек создан (действителен 14 дней)")
                else:
                    messagebox.showwarning("Предупреждение", "Офлайн кошелек уже открыт")
    
    def topup_offline_wallet(self):
        user_id = self.user_select_var.get().split()[0]
        amount = float(self.offline_topup_var.get())
        user = self.system.user_manager.get_user(user_id)
        if user:
            bank = self.system.user_manager.get_bank(user.bank_id)
            if bank:
                if bank.top_up_offline_wallet(user, amount):
                    self.system.database.save_user(user)
                    messagebox.showinfo("Успех", f"Офлайн кошелек пополнен на {amount} ЦР")
                else:
                    messagebox.showerror("Ошибка", "Недостаточно средств или кошелек закрыт/истек срок")
    
    def create_offline_transaction(self):
        sender_id = self.user_select_var.get().split()[0]
        receiver_id = self.offline_receiver_var.get().split()[0] if self.offline_receiver_var.get() else None
        amount = float(self.offline_tx_amount_var.get())
        
        if not receiver_id:
            messagebox.showerror("Ошибка", "Выберите получателя")
            return
        
        otx = self.system.transaction_processor.create_offline_transaction(sender_id, receiver_id, amount)
        if otx:
            messagebox.showinfo("Успех", "Офлайн транзакция создана")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать офлайн транзакцию")
    
    def create_smart_contract(self):
        sender_id = self.user_select_var.get().split()[0]
        receiver_id = self.sc_receiver_var.get().split()[0] if self.sc_receiver_var.get() else None
        amount = float(self.sc_amount_var.get())
        sc_type_str = self.sc_type_var.get()
        
        sc_type_map = {
            "Оплата коммунальных платежей": SmartContractType.UTILITIES,
            "Оплата подписки": SmartContractType.SUBSCRIPTION,
            "Автоплатеж": SmartContractType.AUTOPAYMENT
        }
        sc_type = sc_type_map.get(sc_type_str, SmartContractType.UTILITIES)
        
        if not receiver_id:
            messagebox.showerror("Ошибка", "Выберите получателя")
            return
        
        contract = self.system.transaction_processor.create_smart_contract(
            sender_id, receiver_id, amount, sc_type, 0
        )
        if contract:
            messagebox.showinfo("Успех", "Смарт-контракт создан")
        else:
            messagebox.showerror("Ошибка", "Не удалось создать смарт-контракт")
    
    def request_emission(self):
        bank_id = self.bank_select_var.get()
        amount = float(self.emission_amount_var.get())
        request = self.system.user_manager.banks[bank_id].request_emission(amount)
        approved = self.system.central_bank.process_emission_request(bank_id, amount)
        if approved:
            messagebox.showinfo("Успех", f"Эмиссия одобрена: {amount} ЦР")
        else:
            messagebox.showerror("Ошибка", "Эмиссия отклонена")
    
    def approve_emission(self):
        pass  # Реализация
    
    def reject_emission(self):
        pass  # Реализация
    
    def update_cb_info(self):
        info = f"Центральный банк РФ\n"
        info += f"Общая эмиссия: {self.system.central_bank.total_emission} ЦР\n"
        info += f"Всего пользователей: {len(self.system.user_manager.users)}\n"
        info += f"Всего банков: {len(self.system.user_manager.banks)}\n"
        if self.system.blockchain:
            chain_info = self.system.blockchain.get_chain_info()
            info += f"Блоков в реестре: {chain_info['total_blocks']}\n"
            info += f"Цепочка валидна: {chain_info['chain_valid']}\n"
        self.cb_info_text.delete(1.0, tk.END)
        self.cb_info_text.insert(1.0, info)
    
    def update_users_table(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        
        users = self.system.user_manager.get_all_users()
        for user in users:
            if user.user_type in [UserType.INDIVIDUAL, UserType.LEGAL]:
                self.users_tree.insert("", tk.END, values=(
                    user.user_id,
                    user.user_type.value,
                    f"{user.non_cash_balance:.2f}",
                    user.digital_wallet_status.value,
                    f"{user.digital_wallet_balance:.2f}",
                    user.offline_wallet_status.value,
                    f"{user.offline_wallet_balance:.2f}",
                    user.offline_wallet_activation_time.strftime("%Y-%m-%d %H:%M:%S") if user.offline_wallet_activation_time else "",
                    user.offline_wallet_deactivation_time.strftime("%Y-%m-%d %H:%M:%S") if user.offline_wallet_deactivation_time else ""
                ))
    
    def update_transactions_table(self):
        for item in self.transactions_tree.get_children():
            self.transactions_tree.delete(item)
        
        if self.system.transaction_processor:
            for tx in self.system.transaction_processor.transactions:
                self.transactions_tree.insert("", tk.END, values=(
                    tx.sender_id,
                    tx.receiver_id,
                    tx.transaction_type.value,
                    f"{tx.amount:.2f}",
                    tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    tx.bank_id
                ))
    
    def update_offline_transactions_table(self):
        for item in self.offline_tx_tree.get_children():
            self.offline_tx_tree.delete(item)
        
        if self.system.transaction_processor:
            for otx in self.system.transaction_processor.offline_transactions:
                self.offline_tx_tree.insert("", tk.END, values=(
                    otx.sender_id,
                    otx.receiver_id,
                    f"{otx.amount:.2f}",
                    otx.bank_id,
                    otx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    otx.status.value
                ))
    
    def update_smart_contracts_table(self):
        for item in self.smart_contracts_tree.get_children():
            self.smart_contracts_tree.delete(item)
        
        if self.system.transaction_processor:
            for sc in self.system.transaction_processor.smart_contracts:
                self.smart_contracts_tree.insert("", tk.END, values=(
                    sc.sender_id,
                    sc.receiver_id,
                    f"{sc.amount:.2f}",
                    sc.bank_id,
                    sc.contract_type.value,
                    sc.execution_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Исполнен" if sc.executed else "Ожидает"
                ))
    
    def update_consensus_visualization(self):
        self.consensus_canvas.delete("all")
        
        if not self.system.consensus:
            return
        
        # Визуализация узлов
        node_status = self.system.consensus.get_node_status()
        x_start = 50
        y_center = 200
        node_spacing = 200
        
        # ЦБ в центре
        cb_node = self.system.consensus.nodes.get(self.system.central_bank.bank_id)
        if cb_node:
            x = x_start + node_spacing * 2
            y = y_center
            color = "red" if cb_node.state.value == "Leader" else "lightblue"
            self.consensus_canvas.create_oval(x-30, y-30, x+30, y+30, fill=color, outline="black", width=2)
            self.consensus_canvas.create_text(x, y, text="ЦБ", font=("Arial", 10, "bold"))
            self.consensus_canvas.create_text(x, y+40, text=cb_node.state.value, font=("Arial", 8))
        
        # ФО вокруг
        bank_nodes = [n for n in self.system.consensus.nodes.values() if not n.is_central_bank]
        for i, node in enumerate(bank_nodes):
            angle = (i * 2 * 3.14159) / len(bank_nodes)
            x = x_start + node_spacing * 2 + 150 * (1 + 0.5 * (i % 2)) * (1 if i < len(bank_nodes)/2 else -1)
            y = y_center + 100 * (1 if i < len(bank_nodes)/2 else -1)
            color = "green" if node.state.value == "Leader" else "lightgray"
            self.consensus_canvas.create_oval(x-25, y-25, x+25, y+25, fill=color, outline="black", width=2)
            self.consensus_canvas.create_text(x, y, text=node.node_id[:8], font=("Arial", 8))
            self.consensus_canvas.create_text(x, y+35, text=node.state.value, font=("Arial", 7))
        
        # Обновление таблиц
        for item in self.tx_hash_tree.get_children():
            self.tx_hash_tree.delete(item)
        
        leader = self.system.consensus.get_leader()
        if leader:
            for tx_hash_data in leader.transaction_hashes[-20:]:  # Последние 20
                self.tx_hash_tree.insert("", tk.END, values=(
                    tx_hash_data['hash'][:20] + "...",
                    tx_hash_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    tx_hash_data['term']
                ))
        
        for item in self.consensus_blocks_tree.get_children():
            self.consensus_blocks_tree.delete(item)
        
        if leader:
            for block_data in leader.blocks_formed[-10:]:  # Последние 10
                self.consensus_blocks_tree.insert("", tk.END, values=(
                    block_data['block_id'],
                    block_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    len(block_data.get('transactions', [])),
                    block_data.get('confirmations', 0)
                ))
    
    def update_blockchain_visualization(self):
        self.blockchain_canvas.delete("all")
        
        if not self.system.blockchain:
            return
        
        # Визуализация блоков
        x_start = 50
        y_start = 100
        block_width = 120
        block_height = 80
        block_spacing = 150
        
        blocks = self.system.blockchain.chain
        for i, block in enumerate(blocks[-10:]):  # Последние 10 блоков
            x = x_start + i * block_spacing
            y = y_start
            
            # Блок
            self.blockchain_canvas.create_rectangle(x, y, x+block_width, y+block_height, 
                                                   fill="lightblue", outline="black", width=2)
            self.blockchain_canvas.create_text(x+block_width/2, y+15, text=block.block_id, 
                                              font=("Arial", 9, "bold"))
            self.blockchain_canvas.create_text(x+block_width/2, y+35, 
                                              text=f"Tx: {len(block.transactions)}", 
                                              font=("Arial", 8))
            self.blockchain_canvas.create_text(x+block_width/2, y+55, 
                                              text=block.block_hash[:12] + "...", 
                                              font=("Arial", 7))
            
            # Связь с предыдущим блоком
            if i > 0:
                prev_x = x_start + (i-1) * block_spacing + block_width
                self.blockchain_canvas.create_line(prev_x, y+block_height/2, x, y+block_height/2, 
                                                   arrow=tk.LAST, width=2)
                self.blockchain_canvas.create_text((prev_x+x)/2, y+block_height/2-15, 
                                                  text="prev_hash", font=("Arial", 7))
        
        # Распределение по узлам
        y_nodes = y_start + block_height + 50
        self.blockchain_canvas.create_text(x_start + len(blocks)*block_spacing/2, y_nodes-20, 
                                          text="Распределение блоков по узлам", 
                                          font=("Arial", 10, "bold"))
        
        node_y = y_nodes
        for node_id, node_blocks in list(self.system.blockchain.nodes.items())[:5]:
            self.blockchain_canvas.create_text(x_start, node_y, text=f"{node_id}:", 
                                              font=("Arial", 8), anchor="w")
            self.blockchain_canvas.create_text(x_start + 100, node_y, 
                                              text=f"{len(node_blocks)} блоков", 
                                              font=("Arial", 8))
            node_y += 20
        
        # Обновление таблицы блоков
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)
        
        for block in blocks[-20:]:  # Последние 20
            self.blocks_tree.insert("", tk.END, values=(
                block.block_id,
                block.previous_hash[:20] + "...",
                block.block_hash[:20] + "...",
                block.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                block.node_id or "",
                len(block.transactions)
            ))
    
    def update_metrics(self):
        metrics = self.system.get_metrics()
        
        # Обновление таблицы
        for item in self.metrics_tree.get_children():
            self.metrics_tree.delete(item)
        
        for key, value in metrics.items():
            if isinstance(value, float):
                value_str = f"{value:.2f}"
            else:
                value_str = str(value)
            self.metrics_tree.insert("", tk.END, values=(key, value_str))
        
        # Обновление графиков
        self.metrics_figure.clear()
        
        if self.system.transaction_processor and self.system.blockchain:
            # График 1: Количество транзакций
            ax1 = self.metrics_figure.add_subplot(2, 2, 1)
            tx_times = self.system.transaction_processor.metrics.get('tx_creation_times', [])
            if tx_times:
                ax1.plot(range(len(tx_times)), tx_times)
                ax1.set_title('Время создания транзакций')
                ax1.set_xlabel('Транзакция')
                ax1.set_ylabel('Время (мс)')
            
            # График 2: Время создания блоков
            ax2 = self.metrics_figure.add_subplot(2, 2, 2)
            block_times = self.system.blockchain.metrics.get('block_creation_times', [])
            if block_times:
                ax2.plot(range(len(block_times)), block_times)
                ax2.set_title('Время создания блоков')
                ax2.set_xlabel('Блок')
                ax2.set_ylabel('Время (мс)')
            
            # График 3: Время записи в реестр
            ax3 = self.metrics_figure.add_subplot(2, 2, 3)
            registry_times = self.system.blockchain.metrics.get('block_registry_times', [])
            if registry_times:
                ax3.plot(range(len(registry_times)), registry_times)
                ax3.set_title('Время записи блоков в реестр')
                ax3.set_xlabel('Блок')
                ax3.set_ylabel('Время (мс)')
            
            # График 4: Общая нагрузка
            ax4 = self.metrics_figure.add_subplot(2, 2, 4)
            if metrics.get('total_transactions', 0) > 0:
                ax4.bar(['Транзакции', 'Блоки'], 
                       [metrics.get('total_transactions', 0),
                        len(self.system.blockchain.chain) if self.system.blockchain else 0])
                ax4.set_title('Общая нагрузка системы')
                ax4.set_ylabel('Количество')
        
        self.metrics_figure.tight_layout()
        self.metrics_canvas.draw()
    
    def on_user_updated(self, user):
        pass  # Обновление через таймер
    
    def on_transaction_created(self, transaction):
        pass  # Обновление через таймер
    
    def on_offline_transaction_created(self, offline_tx):
        pass  # Обновление через таймер
    
    def on_smart_contract_created(self, contract):
        pass  # Обновление через таймер
    
    def on_block_created(self, block):
        pass  # Обновление через таймер
    
    def update_timer(self):
        """Таймер обновления данных"""
        try:
            self.update_users_table()
            self.update_transactions_table()
            self.update_offline_transactions_table()
            self.update_smart_contracts_table()
            self.update_consensus_visualization()
            self.update_blockchain_visualization()
            self.update_metrics()
            self.update_user_list()
            self.update_bank_list()
        except:
            pass
        
        self.root.after(2000, self.update_timer)  # Обновление каждые 2 секунды


def main():
    root = tk.Tk()
    app = DigitalRubleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

