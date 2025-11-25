"""
GUI приложение для системы цифрового рубля
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from system import DigitalRubleSystem
from models import UserType, SmartContractType, TransactionType, WalletStatus
from participants import FinancialOrganization
from datetime import datetime
from typing import Optional
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
        self.style = ttk.Style()
        self.fonts = {
            "tab_header": ("Segoe UI", 16, "bold"),
            "section_header": ("Segoe UI", 14, "bold"),
            "body": ("Segoe UI", 12),
            "body_bold": ("Segoe UI", 12, "bold")
        }
        self.style.configure("MgmtHeader.TLabel", font=self.fonts["tab_header"])
        self.style.configure("MgmtBody.TLabel", font=self.fonts["body"])
        self.style.configure("MgmtSection.TLabel", font=("Segoe UI", 13, "bold"))
        self.style.configure("UserHeader.TLabel", font=self.fonts["tab_header"])
        self.style.configure("UserSection.TLabel", font=self.fonts["section_header"])
        self.style.configure("UserBody.TLabel", font=self.fonts["body"])
        self.style.configure("UserBodyBold.TLabel", font=self.fonts["body_bold"])
        self._section_labels = []
        self.user_hint_var = tk.StringVar(value="Создайте пользователей после выбора банка")
        
        self.system = DigitalRubleSystem()
        self.system.initialize_system()
        
        # Регистрация callbacks
        self.system.register_callback('user_updated', self.on_user_updated)
        self.system.register_callback('transaction_created', self.on_transaction_created)
        self.system.register_callback('offline_transaction_created', self.on_offline_transaction_created)
        self.system.register_callback('smart_contract_created', self.on_smart_contract_created)
        self.system.register_callback('block_created', self.on_block_created)
        self.system.register_callback('emission_request', self.on_emission_request)
        self.system.register_callback('emission_approved', self.on_emission_approved)
        self.system.register_callback('block_formation_started', self.on_block_formation_started)
        self.system.register_callback('block_signed', self.on_block_signed)
        self.system.register_callback('block_registered', self.on_block_registered)
        self.system.register_callback('node_failed', self.on_node_failed)
        self.system.register_callback('incident_handled', self.on_incident_handled)
        self.system.register_callback('node_recovered', self.on_node_recovered)
        
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
        self.create_incidents_tab()
        
        # Инициализация значений сценария
        self.on_scenario_selected()
        
        # Таймер обновления
        self.update_timer()
    
    def create_management_tab(self):
        """Вкладка 1: Управление"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Управление")
        
        # Настройки сценария
        ttk.Label(frame, text="Настройки симуляции", style="MgmtHeader.TLabel").pack(pady=10)
        
        config_frame = ttk.LabelFrame(frame, padding=10)
        config_frame.configure(labelwidget=self._create_section_label(config_frame, "Параметры сценария", "MgmtSection.TLabel"))
        config_frame.pack(pady=10, padx=20, fill=tk.X)
        
        # Выбор базового сценария
        ttk.Label(config_frame, text="Базовый сценарий:", style="MgmtBody.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.scenario_var = tk.StringVar(value="1")
        scenario_combo = ttk.Combobox(config_frame, textvariable=self.scenario_var,
                                     values=["1 - Низкая нагрузка", "2 - Средняя нагрузка", "3 - Пиковая нагрузка"],
                                     state="readonly", width=25)
        scenario_combo.grid(row=0, column=1, padx=5, pady=5)
        scenario_combo.bind("<<ComboboxSelected>>", self.on_scenario_selected)
        
        # Настройка параметров
        ttk.Label(config_frame, text="Количество пользователей:", style="MgmtBody.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.custom_users_var = tk.StringVar(value="1000")
        ttk.Entry(config_frame, textvariable=self.custom_users_var, width=15).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Количество ФО:", style="MgmtBody.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.custom_banks_var = tk.StringVar(value="5")
        ttk.Entry(config_frame, textvariable=self.custom_banks_var, width=15).grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Транзакций в минуту:", style="MgmtBody.TLabel").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.custom_tx_per_min_var = tk.StringVar(value="2075")
        ttk.Entry(config_frame, textvariable=self.custom_tx_per_min_var, width=15).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(config_frame, text="Длительность (минуты):", style="MgmtBody.TLabel").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.custom_duration_var = tk.StringVar(value="2")
        ttk.Entry(config_frame, textvariable=self.custom_duration_var, width=15).grid(row=4, column=1, padx=5, pady=5)
        
        # Управление симуляцией
        control_frame = ttk.LabelFrame(frame, padding=10)
        control_frame.configure(labelwidget=self._create_section_label(control_frame, "Управление симуляцией", "MgmtSection.TLabel"))
        control_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.sim_button = ttk.Button(control_frame, text="Запустить симуляцию", 
                                     command=self.start_simulation)
        self.sim_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(control_frame, text="Остановить симуляцию", 
                  command=self.stop_simulation).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Таймер симуляции
        timer_frame = ttk.LabelFrame(frame, padding=10)
        timer_frame.configure(labelwidget=self._create_section_label(timer_frame, "Таймер симуляции", "MgmtSection.TLabel"))
        timer_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.timer_label = ttk.Label(timer_frame, text="Время: 00:00 / 02:00", 
                                     font=("Segoe UI", 18, "bold"))
        self.timer_label.pack(pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(timer_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(pady=5)
        
        # Статус
        self.status_label = ttk.Label(frame, text="Статус: Готов к работе", 
                                     font=("Segoe UI", 12, "bold"))
        self.status_label.pack(pady=10)
    
    def _create_section_label(self, parent, text, style="UserSection.TLabel"):
        """Создание подписей для LabelFrame с удержанием ссылки"""
        label = ttk.Label(parent, text=text, style=style)
        self._section_labels.append(label)
        return label
    
    def create_user_tab(self):
        """Вкладка 2: Пользователь"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Пользователь")

        ttk.Label(frame, text="Управление пользовательскими кошельками", 
                  style="UserHeader.TLabel").pack(pady=(10, 0))
        ttk.Label(
            frame,
            text="Создайте или выберите пользователя, чтобы открывать кошельки, пополнять балансы и выполнять онлайн/офлайн операции.",
            style="UserBody.TLabel",
            wraplength=1100,
            justify=tk.LEFT
        ).pack(pady=(0, 5), padx=10)
        ttk.Label(frame, textvariable=self.user_hint_var, style="UserBodyBold.TLabel",
                  wraplength=1100, justify=tk.LEFT).pack(pady=(0, 10), padx=10)
        
        # Создание пользователей
        create_frame = ttk.LabelFrame(frame, padding=10)
        create_frame.configure(labelwidget=self._create_section_label(create_frame, "Создание пользователей"))
        create_frame.pack(pady=10, padx=10, fill=tk.X)
        
        create_inner = ttk.Frame(create_frame)
        create_inner.pack(pady=5, fill=tk.X)
        create_inner.grid_columnconfigure(5, weight=1)
        
        ttk.Label(create_inner, text="Количество:", style="UserBody.TLabel").grid(row=0, column=0, padx=5, pady=2)
        self.user_count_var = tk.StringVar(value="5")
        ttk.Entry(create_inner, textvariable=self.user_count_var, width=10).grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(create_inner, text="Тип:", style="UserBody.TLabel").grid(row=0, column=2, padx=5, pady=2)
        self.user_type_var = tk.StringVar(value="Физическое лицо")
        user_type_combo = ttk.Combobox(
            create_inner,
            textvariable=self.user_type_var,
            values=["Физическое лицо", "Юридическое лицо"],
            state="readonly",
            width=20
        )
        user_type_combo.grid(row=0, column=3, padx=5, pady=2)
        
        ttk.Label(create_inner, text="Банк:", style="UserBody.TLabel").grid(row=0, column=4, padx=5, pady=2)
        self.user_bank_var = tk.StringVar()
        self.user_bank_combo = ttk.Combobox(create_inner, textvariable=self.user_bank_var, width=18, state="readonly")
        self.user_bank_combo.grid(row=0, column=5, padx=5, pady=2, sticky="w")
        
        ttk.Button(create_inner, text="Создать пользователей", command=self.create_users_manual).grid(
            row=0, column=6, padx=5, pady=2
        )
        
        ttk.Label(
            create_frame,
            text="Совет: если банки не созданы, перейдите на вкладку «Финансовая организация» или создайте базовый банк автоматически.",
            style="UserBody.TLabel",
            wraplength=1200,
            justify=tk.LEFT
        ).pack(pady=(8, 0))
        
        # Выбор пользователя
        user_select_frame = ttk.LabelFrame(frame, padding=10)
        user_select_frame.configure(labelwidget=self._create_section_label(user_select_frame, "Выбор пользователя"))
        user_select_frame.pack(pady=10, padx=10, fill=tk.X)
        
        selection_inner = ttk.Frame(user_select_frame)
        selection_inner.pack(fill=tk.X)
        selection_inner.columnconfigure(1, weight=1)
        
        ttk.Label(selection_inner, text="Пользователь:", style="UserBody.TLabel").grid(row=0, column=0, padx=5, pady=2)
        self.user_select_var = tk.StringVar()
        self.user_select_combo = ttk.Combobox(
            selection_inner, textvariable=self.user_select_var, state="readonly", width=40
        )
        self.user_select_combo.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
        ttk.Button(selection_inner, text="Обновить список", command=self.update_user_list).grid(
            row=0, column=2, padx=5, pady=2
        )
        
        self.user_status_label = ttk.Label(
            user_select_frame,
            text="Нет выбранного пользователя",
            style="UserBodyBold.TLabel"
        )
        self.user_status_label.pack(pady=(6, 0), anchor="w")
        
        # Функции пользователя
        func_frame = ttk.LabelFrame(frame, padding=10)
        func_frame.configure(labelwidget=self._create_section_label(func_frame, "Функции пользователя"))
        func_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        actions_container = ttk.Frame(func_frame)
        actions_container.pack(fill=tk.BOTH, expand=True)
        
        wallet_column = ttk.Frame(actions_container)
        wallet_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        tx_column = ttk.Frame(actions_container)
        tx_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Создание цифрового кошелька
        ttk.Label(wallet_column, text="Цифровой кошелек", style="UserSection.TLabel").pack(anchor="w", pady=(0, 4))
        ttk.Button(wallet_column, text="Создать цифровой кошелек", 
                  command=self.create_digital_wallet).pack(pady=5, fill=tk.X)
        
        topup_frame = ttk.Frame(wallet_column)
        topup_frame.pack(pady=5, fill=tk.X)
        ttk.Label(topup_frame, text="Сумма пополнения:", style="UserBody.TLabel").pack(side=tk.LEFT, padx=5)
        self.topup_amount_var = tk.StringVar(value="1000")
        ttk.Entry(topup_frame, textvariable=self.topup_amount_var, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(topup_frame, text="Пополнить", command=self.topup_digital_wallet).pack(side=tk.LEFT, padx=5)
        
        # Офлайн кошелек
        ttk.Separator(wallet_column, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(wallet_column, text="Офлайн кошелек", style="UserSection.TLabel").pack(anchor="w", pady=(0, 4))
        
        ttk.Button(wallet_column, text="Открыть офлайн кошелек", 
                  command=self.create_offline_wallet).pack(pady=5, fill=tk.X)
        ttk.Label(wallet_column, text="Сумма пополнения:", style="UserBody.TLabel").pack(anchor="w", padx=5)
        self.offline_topup_var = tk.StringVar(value="200")
        ttk.Entry(wallet_column, textvariable=self.offline_topup_var, width=15).pack(padx=5, pady=5, anchor="w")
        ttk.Button(wallet_column, text="Пополнить офлайн кошелек", 
                  command=self.topup_offline_wallet).pack(pady=5, fill=tk.X)
        
        ttk.Label(wallet_column, text="Отправитель офлайн-перевода:", style="UserBody.TLabel").pack(anchor="w", padx=5, pady=(10, 2))
        self.offline_sender_var = tk.StringVar()
        self.offline_sender_combo = ttk.Combobox(
            wallet_column, textvariable=self.offline_sender_var, width=30, state="readonly"
        )
        self.offline_sender_combo.pack(padx=5, pady=2, anchor="w")
        
        ttk.Label(wallet_column, text="Получатель офлайн-перевода:", style="UserBody.TLabel").pack(anchor="w", padx=5, pady=(4, 2))
        self.offline_receiver_var = tk.StringVar()
        self.offline_receiver_combo = ttk.Combobox(
            wallet_column, textvariable=self.offline_receiver_var, width=30, state="readonly"
        )
        self.offline_receiver_combo.pack(padx=5, pady=2, anchor="w")
        
        ttk.Label(wallet_column, text="Сумма перевода:", style="UserBody.TLabel").pack(anchor="w", padx=5, pady=(4, 2))
        self.offline_tx_amount_var = tk.StringVar(value="50")
        ttk.Entry(wallet_column, textvariable=self.offline_tx_amount_var, width=15).pack(padx=5, pady=2, anchor="w")
        ttk.Button(wallet_column, text="Создать офлайн транзакцию", 
                  command=self.create_offline_transaction).pack(pady=5, fill=tk.X)
        
        # Онлайн транзакция
        ttk.Label(tx_column, text="Онлайн транзакции", style="UserSection.TLabel").pack(anchor="w", pady=(0, 4))
        tx_frame = ttk.Frame(tx_column)
        tx_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tx_frame, text="Отправитель:", style="UserBody.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tx_sender_var = tk.StringVar()
        self.tx_sender_combo = ttk.Combobox(tx_frame, textvariable=self.tx_sender_var, width=30, state="readonly")
        self.tx_sender_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(tx_frame, text="Получатель:", style="UserBody.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.tx_receiver_var = tk.StringVar()
        self.tx_receiver_combo = ttk.Combobox(tx_frame, textvariable=self.tx_receiver_var, width=30, state="readonly")
        self.tx_receiver_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(tx_frame, text="Сумма:", style="UserBody.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.tx_amount_var = tk.StringVar(value="100")
        ttk.Entry(tx_frame, textvariable=self.tx_amount_var, width=15).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(tx_frame, text="Создать онлайн транзакцию", 
                  command=self.create_user_transaction).grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")
        tx_frame.grid_columnconfigure(1, weight=1)
        
        # Смарт-контракт
        ttk.Separator(tx_column, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(tx_column, text="Смарт-контракты", style="UserSection.TLabel").pack(anchor="w", pady=(0, 4))
        sc_frame = ttk.Frame(tx_column)
        sc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(sc_frame, text="Тип:", style="UserBody.TLabel").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.sc_type_var = tk.StringVar(value="Оплата коммунальных платежей")
        sc_type_combo = ttk.Combobox(sc_frame, textvariable=self.sc_type_var,
                                    values=["Оплата коммунальных платежей", "Оплата подписки", "Автоплатеж"],
                                    state="readonly", width=30)
        sc_type_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(sc_frame, text="Отправитель (физлицо):", style="UserBody.TLabel").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.sc_sender_var = tk.StringVar()
        self.sc_sender_combo = ttk.Combobox(sc_frame, textvariable=self.sc_sender_var, width=30, state="readonly")
        self.sc_sender_combo.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(sc_frame, text="Получатель (юрлицо/гос):", style="UserBody.TLabel").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sc_receiver_var = tk.StringVar()
        self.sc_receiver_combo = ttk.Combobox(sc_frame, textvariable=self.sc_receiver_var, width=30, state="readonly")
        self.sc_receiver_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(sc_frame, text="Сумма:", style="UserBody.TLabel").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.sc_amount_var = tk.StringVar(value="1000")
        ttk.Entry(sc_frame, textvariable=self.sc_amount_var, width=15).grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Button(sc_frame, text="Создать смарт-контракт", 
                  command=self.create_smart_contract).grid(row=4, column=0, columnspan=2, pady=5, sticky="ew")
        sc_frame.grid_columnconfigure(1, weight=1)
    
    def create_bank_tab(self):
        """Вкладка 3: Финансовая организация"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Финансовая организация")
        
        # Создание банков
        create_frame = ttk.LabelFrame(frame, text="Создание банков (ФО)")
        create_frame.pack(pady=10, padx=10, fill=tk.X)
        
        create_inner = ttk.Frame(create_frame)
        create_inner.pack(pady=5)
        
        ttk.Label(create_inner, text="Количество:").grid(row=0, column=0, padx=5)
        self.bank_count_var = tk.StringVar(value="5")
        ttk.Entry(create_inner, textvariable=self.bank_count_var, width=10).grid(row=0, column=1, padx=5)
        
        ttk.Button(create_inner, text="Создать банки", 
                  command=self.create_banks_manual).grid(row=0, column=2, padx=5)
        
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
        self.bank_select_combo.bind("<<ComboboxSelected>>", lambda e: self.update_bank_data())
        
        # Запрос на эмиссию
        emission_frame = ttk.LabelFrame(frame, text="Запрос на эмиссию")
        emission_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(emission_frame, text="Сумма эмиссии:").grid(row=0, column=0, padx=5, pady=5)
        self.emission_amount_var = tk.StringVar(value="100000")
        ttk.Entry(emission_frame, textvariable=self.emission_amount_var, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(emission_frame, text="Отправить запрос", 
                  command=self.request_emission).grid(row=0, column=2, padx=5)
        
        # Транзакции банка
        tx_frame = ttk.LabelFrame(frame, text="Транзакции через этот банк")
        tx_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Таблица транзакций
        columns = ("ID", "Отправитель", "Получатель", "Сумма", "Тип", "Время", "Статус")
        self.bank_tx_tree = ttk.Treeview(tx_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.bank_tx_tree.heading(col, text=col)
            self.bank_tx_tree.column(col, width=120)
        self.bank_tx_tree.pack(fill=tk.BOTH, expand=True)
        
        # Этапы голосования за подписание блоков
        voting_frame = ttk.LabelFrame(frame, text="Этапы голосования за подписание блоков")
        voting_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID блока", "Время", "Голос", "Статус", "Результат")
        self.bank_voting_tree = ttk.Treeview(voting_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.bank_voting_tree.heading(col, text=col)
            self.bank_voting_tree.column(col, width=150)
        self.bank_voting_tree.pack(fill=tk.BOTH, expand=True)
        
        # Блоки хранящиеся в ФО
        blocks_frame = ttk.LabelFrame(frame, text="Блоки хранящиеся в этом ФО")
        blocks_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID блока", "Хеш", "Предыдущий хеш", "Транзакций", "Время", "Подписан")
        self.bank_blocks_tree = ttk.Treeview(blocks_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.bank_blocks_tree.heading(col, text=col)
            self.bank_blocks_tree.column(col, width=150)
        self.bank_blocks_tree.pack(fill=tk.BOTH, expand=True)
        
        # Кнопка обновления данных
        ttk.Button(frame, text="Обновить данные банка", 
                  command=self.update_bank_data).pack(pady=5)
    
    def create_central_bank_tab(self):
        """Вкладка 4: Центральный банк"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Центральный банк")
        
        # Запросы на эмиссию
        emission_frame = ttk.LabelFrame(frame, text="Запросы на эмиссию от банков")
        emission_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Банк", "Сумма", "Время", "Статус")
        self.cb_emission_tree = ttk.Treeview(emission_frame, columns=columns, show="headings", height=8)
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
        
        # Транзакции
        tx_frame = ttk.LabelFrame(frame, text="Транзакции")
        tx_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("ID", "Отправитель", "Получатель", "Сумма", "Тип", "Время", "Статус")
        self.cb_tx_tree = ttk.Treeview(tx_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.cb_tx_tree.heading(col, text=col)
            self.cb_tx_tree.column(col, width=120)
        self.cb_tx_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Формирование блоков
        block_formation_frame = ttk.LabelFrame(frame, text="Формирование блоков")
        block_formation_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Время", "Стадия", "Кол-во транзакций", "ID блока")
        self.cb_block_formation_tree = ttk.Treeview(block_formation_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.cb_block_formation_tree.heading(col, text=col)
            self.cb_block_formation_tree.column(col, width=150)
        self.cb_block_formation_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Подписание блоков
        signing_frame = ttk.LabelFrame(frame, text="Подписание блоков")
        signing_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Время", "ID блока", "Кол-во подписей", "Статус")
        self.cb_signing_tree = ttk.Treeview(signing_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.cb_signing_tree.heading(col, text=col)
            self.cb_signing_tree.column(col, width=150)
        self.cb_signing_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Запись в реестр
        registry_frame = ttk.LabelFrame(frame, text="Запись блоков в реестр")
        registry_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Время", "ID блока", "Узел", "Статус")
        self.cb_registry_tree = ttk.Treeview(registry_frame, columns=columns, show="headings", height=8)
        for col in columns:
            self.cb_registry_tree.heading(col, text=col)
            self.cb_registry_tree.column(col, width=150)
        self.cb_registry_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Общая информация
        info_frame = ttk.LabelFrame(frame, text="Общая информация")
        info_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.cb_info_text = scrolledtext.ScrolledText(info_frame, height=8, wrap=tk.WORD)
        self.cb_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Button(info_frame, text="Обновить информацию", 
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
        
        # Панель управления zoom/pan
        control_panel = ttk.Frame(viz_frame)
        control_panel.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_panel, text="Управление:").pack(side=tk.LEFT, padx=5)
        ttk.Button(control_panel, text="Приблизить (+)", command=self.consensus_zoom_in).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_panel, text="Отдалить (-)", command=self.consensus_zoom_out).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_panel, text="Сброс", command=self.consensus_reset_view).pack(side=tk.LEFT, padx=2)
        ttk.Label(control_panel, text="Масштаб:").pack(side=tk.LEFT, padx=10)
        self.consensus_scale_var = tk.StringVar(value="1.0x")
        ttk.Label(control_panel, textvariable=self.consensus_scale_var).pack(side=tk.LEFT, padx=5)
        
        # Canvas с прокруткой
        canvas_frame = ttk.Frame(viz_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollable canvas
        self.consensus_canvas = tk.Canvas(canvas_frame, bg="white", width=1000, height=600, scrollregion=(0, 0, 2000, 2000))
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.consensus_canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.consensus_canvas.xview)
        self.consensus_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.consensus_canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Переменные для zoom и pan
        self.consensus_zoom = 1.0
        self.consensus_pan_x = 0
        self.consensus_pan_y = 0
        
        # Привязка событий мыши для pan
        self.consensus_canvas.bind("<ButtonPress-1>", self.consensus_start_pan)
        self.consensus_canvas.bind("<B1-Motion>", self.consensus_pan)
        self.consensus_canvas.bind("<MouseWheel>", self.consensus_on_mousewheel)
        self.consensus_canvas.bind("<Button-4>", self.consensus_on_mousewheel)
        self.consensus_canvas.bind("<Button-5>", self.consensus_on_mousewheel)
        
        # Таблица хешей транзакций
        hash_frame = ttk.LabelFrame(frame, text="Хеши транзакций")
        hash_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        columns = ("Хеш", "Время", "Кворум")
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
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10, padx=10)
        ttk.Button(button_frame, text="🔄 Обновить визуализацию", 
                  command=self.update_consensus_visualization, width=25).pack(side=tk.LEFT, padx=5)
    
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
        
        columns = ("ID", "Родитель ID", "Предыдущий хеш", "Хеш блока", "Время", "Узел", "Транзакций", "Связь")
        self.blocks_tree = ttk.Treeview(info_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.blocks_tree.heading(col, text=col)
            self.blocks_tree.column(col, width=120)
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
        
        # Кнопка обновления метрик
        button_frame = ttk.Frame(frame)
        button_frame.pack(pady=10, padx=10)
        ttk.Button(button_frame, text="Обновить метрики", 
                  command=self.update_metrics, width=25).pack(side=tk.LEFT, padx=5)
        
        # Инициализация метрик при создании вкладки
        self.update_metrics()
    
    def create_incidents_tab(self):
        """Вкладка 12: Инциденты"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Инциденты")
        
        # Сценарии инцидентов
        scenarios_frame = ttk.LabelFrame(frame, text="Сценарии инцидентов")
        scenarios_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        # Таблица сценариев
        columns = ("Сценарий", "N узлов", "Отказавшие узлы", "Кворум достигнут", "Время восстановления", "Работоспособность")
        self.incidents_tree = ttk.Treeview(scenarios_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.incidents_tree.heading(col, text=col)
            self.incidents_tree.column(col, width=150)
        self.incidents_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Заполнение таблицы
        scenarios_data = [
            ("Штатный режим", "5 (1 ЦБ + 4 ФО)", "—", "Да (5/5)", "—", "Штатный режим"),
            ("Отказ ЦБ РФ", "5", "ЦБ", "Да (3/4 ФО)", "1.8 ± 0.3 с", "Штатный режим"),
            ("Отказ 1 ФО", "5", "ФО-3", "Да (4/5)", "<0.1 с", "Штатный режим"),
            ("Отказ 2 ФО", "5", "ФО-2, ФО-4", "Да (3/5)", "<0.1 с", "Штатный режим"),
            ("Отказ ЦБ + 2 ФО", "5", "ЦБ, ФО-1, ФО-3", "Нет (2/5)", "—", "Аварийная остановка")
        ]
        for data in scenarios_data:
            self.incidents_tree.insert("", tk.END, values=data)
        
        # Управление инцидентами
        control_frame = ttk.LabelFrame(frame, text="Симуляция инцидента")
        control_frame.pack(pady=10, padx=10, fill=tk.X)
        
        ttk.Label(control_frame, text="Выберите сценарий:").pack(side=tk.LEFT, padx=5)
        self.incident_type_var = tk.StringVar()
        incident_combo = ttk.Combobox(control_frame, textvariable=self.incident_type_var,
                                     values=["cb_failure - Отказ ЦБ РФ", 
                                            "fo_1_failure - Отказ 1 ФО", 
                                            "fo_2_failure - Отказ 2 ФО", 
                                            "cb_fo_2_failure - Отказ ЦБ + 2 ФО (только ручной)"],
                                     state="readonly", width=40)
        incident_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Запустить симуляцию инцидента", 
                  command=self.simulate_incident).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(control_frame, text="Примечание: Автоматические инциденты происходят каждые 700-1200 транзакций", 
                 font=("Arial", 8)).pack(side=tk.LEFT, padx=10)
        
        # Результаты
        results_frame = ttk.LabelFrame(frame, text="Результаты симуляции")
        results_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.incidents_results = scrolledtext.ScrolledText(results_frame, height=15, wrap=tk.WORD)
        self.incidents_results.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Методы обработки событий
    def create_users_manual(self):
        try:
            count = int(self.user_count_var.get())
            if count <= 0:
                raise ValueError
            user_type_str = self.user_type_var.get()
            user_type = UserType.INDIVIDUAL if user_type_str == "Физическое лицо" else UserType.LEGAL
            banks = list(self.system.user_manager.banks.keys())
            if not banks:
                created = self.system.create_banks(1)
                banks = created
                self.update_bank_list()
            bank_id = self.user_bank_var.get() or (banks[0] if banks else None)
            if not bank_id:
                messagebox.showerror("Ошибка", "Создайте хотя бы один банк во вкладке ФО")
                return
            user_ids = []
            for _ in range(count):
                user_id = self.system.create_user_for_bank(user_type, bank_id)
                user_ids.append(user_id)
            messagebox.showinfo("Успех", f"Создано пользователей: {len(user_ids)} (банк {bank_id})")
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
    
    def on_scenario_selected(self, event=None):
        """Обновление параметров при выборе сценария"""
        scenario = int(self.scenario_var.get().split()[0])
        scenarios = {
            1: {'users': 1000, 'banks': 5, 'tx_per_minute': 2075, 'duration': 2},
            2: {'users': 10000, 'banks': 10, 'tx_per_minute': 20900, 'duration': 2},
            3: {'users': 50000, 'banks': 15, 'tx_per_minute': 104250, 'duration': 2}
        }
        config = scenarios.get(scenario, scenarios[1])
        self.custom_users_var.set(str(config['users']))
        self.custom_banks_var.set(str(config['banks']))
        self.custom_tx_per_min_var.set(str(config['tx_per_minute']))
        self.custom_duration_var.set(str(config['duration']))
    
    def start_simulation(self):
        try:
            scenario = int(self.scenario_var.get().split()[0])
            custom_config = {
                'users': int(self.custom_users_var.get()),
                'banks': int(self.custom_banks_var.get()),
                'tx_per_minute': int(self.custom_tx_per_min_var.get()),
                'duration_minutes': int(self.custom_duration_var.get())
            }
            self.system.start_simulation(scenario, custom_config)
            self.status_label.config(text="Статус: Симуляция запущена")
            self.sim_button.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def stop_simulation(self):
        self.system.stop_simulation()
        self.status_label.config(text="Статус: Симуляция остановлена")
        self.sim_button.config(state="normal")
        self.timer_label.config(text="Время: 00:00 / 00:00")
        self.progress_var.set(0)
    
    def update_user_list(self):
        users = self.system.user_manager.get_all_users()
        filtered_users = [u for u in users if u.user_type in [UserType.INDIVIDUAL, UserType.LEGAL]]
        user_list = [f"{u.user_id} ({u.user_type.value})" for u in filtered_users]
        self.user_select_combo['values'] = user_list
        if user_list:
            if not self.user_select_var.get():
                self.user_select_combo.current(0)
                self.user_select_var.set(user_list[0])
            if hasattr(self, 'user_status_label'):
                self.user_status_label.config(text=f"Выбран: {self.user_select_var.get()}")
        else:
            if hasattr(self, 'user_status_label'):
                self.user_status_label.config(text="Нет доступных пользователей")
        
        # Обновление списков для всех типов транзакций
        if hasattr(self, 'tx_sender_combo'):
            self.tx_sender_combo['values'] = user_list
        if hasattr(self, 'tx_receiver_combo'):
            self.tx_receiver_combo['values'] = user_list
        if hasattr(self, 'offline_sender_combo'):
            self.offline_sender_combo['values'] = user_list
        if hasattr(self, 'offline_receiver_combo'):
            self.offline_receiver_combo['values'] = user_list
        
        # Для смарт-контрактов: отправитель - только физлица, получатель - только юрлица/гос
        individual_list = [f"{u.user_id} ({u.user_type.value})" for u in filtered_users 
                          if u.user_type == UserType.INDIVIDUAL]
        legal_list = [f"{u.user_id} ({u.user_type.value})" for u in users 
                     if u.user_type in [UserType.LEGAL, UserType.CENTRAL_BANK]]
        if hasattr(self, 'sc_sender_combo'):
            self.sc_sender_combo['values'] = individual_list
        if hasattr(self, 'sc_receiver_combo'):
            self.sc_receiver_combo['values'] = legal_list
        
        if hasattr(self, 'user_hint_var'):
            self.user_hint_var.set(
                f"Банков: {len(self.system.user_manager.banks)} | Пользователей: {len(filtered_users)}"
            )
    
    def update_bank_list(self):
        banks = list(self.system.user_manager.banks.keys())
        self.bank_select_combo['values'] = banks
        if banks:
            self.bank_select_combo.current(0)
        if hasattr(self, 'user_bank_combo'):
            self.user_bank_combo['values'] = banks
            if banks and not self.user_bank_var.get():
                self.user_bank_combo.current(0)
        if hasattr(self, 'user_hint_var'):
            self.user_hint_var.set(f"Банков доступно: {len(banks)}. Создайте пользователей и выберите их ниже.")
    
    def _get_selected_user_id(self, error_message: str = "Выберите пользователя") -> Optional[str]:
        """Безопасное извлечение выбранного пользователя"""
        user_entry = self.user_select_var.get() if hasattr(self, 'user_select_var') else ""
        if not user_entry:
            messagebox.showerror("Ошибка", error_message)
            return None
        return user_entry.split()[0]
    
    def _extract_user_id(self, value: str) -> Optional[str]:
        """Извлечение user_id из строки комбобокса"""
        return value.split()[0] if value else None
    
    def create_digital_wallet(self):
        user_id = self._get_selected_user_id()
        if not user_id:
            return
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
        user_id = self._get_selected_user_id()
        if not user_id:
            return
        try:
            amount = float(self.topup_amount_var.get())
            user = self.system.user_manager.get_user(user_id)
            if user:
                bank = self.system.user_manager.get_bank(user.bank_id)
                if bank:
                    if bank.top_up_digital_wallet(user, amount, self.system.transaction_processor):
                        self.system.database.save_user(user)
                        messagebox.showinfo("Успех", f"Кошелек пополнен на {amount} ЦР")
                    else:
                        messagebox.showerror("Ошибка", "Недостаточно средств или кошелек закрыт")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
    
    def create_user_transaction(self):
        try:
            sender_id = self._extract_user_id(self.tx_sender_var.get())
            receiver_id = self._extract_user_id(self.tx_receiver_var.get())
            
            if not sender_id:
                messagebox.showerror("Ошибка", "Выберите отправителя")
                return
            if not receiver_id:
                messagebox.showerror("Ошибка", "Выберите получателя")
                return
            
            if sender_id == receiver_id:
                messagebox.showerror("Ошибка", "Отправитель и получатель не могут быть одинаковыми")
                return
            
            amount = float(self.tx_amount_var.get())
            tx = self.system.transaction_processor.create_online_transaction(sender_id, receiver_id, amount)
            if tx:
                messagebox.showinfo("Успех", "Транзакция создана")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать транзакцию")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def create_offline_wallet(self):
        user_id = self._get_selected_user_id()
        if not user_id:
            return
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
        user_id = self._get_selected_user_id()
        if not user_id:
            return
        try:
            amount = float(self.offline_topup_var.get())
            user = self.system.user_manager.get_user(user_id)
            if user:
                bank = self.system.user_manager.get_bank(user.bank_id)
                if bank:
                    if bank.top_up_offline_wallet(user, amount, self.system.transaction_processor):
                        self.system.database.save_user(user)
                        messagebox.showinfo("Успех", f"Офлайн кошелек пополнен на {amount} ЦР")
                    else:
                        messagebox.showerror("Ошибка", "Недостаточно средств или кошелек закрыт/истек срок")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
    
    def create_offline_transaction(self):
        try:
            sender_id = self._extract_user_id(self.offline_sender_var.get())
            receiver_id = self._extract_user_id(self.offline_receiver_var.get())
            
            if not sender_id:
                messagebox.showerror("Ошибка", "Выберите отправителя")
                return
            if not receiver_id:
                messagebox.showerror("Ошибка", "Выберите получателя")
                return
            
            if sender_id == receiver_id:
                messagebox.showerror("Ошибка", "Отправитель и получатель не могут быть одинаковыми")
                return
            
            amount = float(self.offline_tx_amount_var.get())
            otx = self.system.transaction_processor.create_offline_transaction(sender_id, receiver_id, amount)
            if otx:
                messagebox.showinfo("Успех", "Офлайн транзакция создана")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать офлайн транзакцию")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def create_smart_contract(self):
        try:
            sender_id = self._extract_user_id(self.sc_sender_var.get())
            receiver_id = self._extract_user_id(self.sc_receiver_var.get())
            
            if not sender_id:
                messagebox.showerror("Ошибка", "Выберите отправителя (физическое лицо)")
                return
            if not receiver_id:
                messagebox.showerror("Ошибка", "Выберите получателя (юридическое лицо или гос учреждение)")
                return
            
            # Проверка типа отправителя
            sender = self.system.user_manager.get_user(sender_id)
            if not sender or sender.user_type != UserType.INDIVIDUAL:
                messagebox.showerror("Ошибка", "Отправитель должен быть физическим лицом")
                return
            
            # Проверка типа получателя
            receiver = self.system.user_manager.get_user(receiver_id)
            if not receiver or receiver.user_type not in [UserType.LEGAL, UserType.CENTRAL_BANK]:
                messagebox.showerror("Ошибка", "Получатель должен быть юридическим лицом или государственным учреждением")
                return
            
            amount = float(self.sc_amount_var.get())
            sc_type_str = self.sc_type_var.get()
            
            sc_type_map = {
                "Оплата коммунальных платежей": SmartContractType.UTILITIES,
                "Оплата подписки": SmartContractType.SUBSCRIPTION,
                "Автоплатеж": SmartContractType.AUTOPAYMENT
            }
            sc_type = sc_type_map.get(sc_type_str, SmartContractType.UTILITIES)
            
            contract = self.system.transaction_processor.create_smart_contract(
                sender_id, receiver_id, amount, sc_type, 0
            )
            if contract:
                messagebox.showinfo("Успех", "Смарт-контракт создан")
            else:
                messagebox.showerror("Ошибка", "Не удалось создать смарт-контракт")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def request_emission(self):
        try:
            bank_id = self.bank_select_var.get()
            if not bank_id:
                raise ValueError("Выберите банк для запроса эмиссии")
            amount = float(self.emission_amount_var.get())
            record = self.system.submit_emission_request(bank_id, amount, manual=True)
            approved = self.system.finalize_emission_request(record)
            if approved:
                messagebox.showinfo("Успех", f"Эмиссия одобрена: {amount} ЦР")
            else:
                messagebox.showwarning("Информация", "ЦБ отклонил запрос на эмиссию")
            self.update_cb_tables()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def approve_emission(self):
        """Одобрение выбранного запроса на эмиссию"""
        try:
            selected_item = self.cb_emission_tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запрос на эмиссию из таблицы")
                return
            
            item_values = self.cb_emission_tree.item(selected_item[0], 'values')
            if not item_values:
                return
            
            bank_id = item_values[0]
            amount_str = item_values[1]
            status = item_values[3]
            
            if status in ['Одобрено', 'Отклонено']:
                messagebox.showinfo("Информация", "Этот запрос уже обработан")
                return
            
            # Найти запрос в БД
            emission_records = self.system.database.get_recent_emission_requests(limit=100)
            for req in emission_records:
                if req.bank_id == bank_id and abs(req.amount - float(amount_str)) < 0.01 and req.status == 'pending':
                    # Одобрить запрос
                    approved = self.system.central_bank.process_emission_request(req.bank_id, req.amount)
                    if approved:
                        self.system.database.update_emission_request_status(req.id, 'approved', True)
                        messagebox.showinfo("Успех", f"Эмиссия одобрена: {req.amount:.2f} ЦР для банка {req.bank_id}")
                    else:
                        self.system.database.update_emission_request_status(req.id, 'rejected', False)
                        messagebox.showwarning("Отклонено", "ЦБ отклонил запрос на эмиссию")
                    self.update_cb_tables()
                    return
            
            messagebox.showwarning("Предупреждение", "Запрос не найден в базе данных")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при одобрении эмиссии: {str(e)}")
    
    def reject_emission(self):
        """Отклонение выбранного запроса на эмиссию"""
        try:
            selected_item = self.cb_emission_tree.selection()
            if not selected_item:
                messagebox.showwarning("Предупреждение", "Выберите запрос на эмиссию из таблицы")
                return
            
            item_values = self.cb_emission_tree.item(selected_item[0], 'values')
            if not item_values:
                return
            
            bank_id = item_values[0]
            amount_str = item_values[1]
            status = item_values[3]
            
            if status in ['Одобрено', 'Отклонено']:
                messagebox.showinfo("Информация", "Этот запрос уже обработан")
                return
            
            # Найти запрос в БД
            emission_records = self.system.database.get_recent_emission_requests(limit=100)
            for req in emission_records:
                if req.bank_id == bank_id and abs(req.amount - float(amount_str)) < 0.01 and req.status == 'pending':
                    # Отклонить запрос
                    self.system.database.update_emission_request_status(req.id, 'rejected', False)
                    messagebox.showinfo("Информация", f"Запрос на эмиссию отклонен: {req.amount:.2f} ЦР для банка {req.bank_id}")
                    self.update_cb_tables()
                    return
            
            messagebox.showwarning("Предупреждение", "Запрос не найден в базе данных")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при отклонении эмиссии: {str(e)}")
    
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
    
    def consensus_zoom_in(self):
        """Приближение консенсуса"""
        self.consensus_zoom = min(self.consensus_zoom * 1.2, 3.0)
        self.consensus_scale_var.set(f"{self.consensus_zoom:.1f}x")
        self.update_consensus_visualization()
    
    def consensus_zoom_out(self):
        """Отдаление консенсуса"""
        self.consensus_zoom = max(self.consensus_zoom / 1.2, 0.5)
        self.consensus_scale_var.set(f"{self.consensus_zoom:.1f}x")
        self.update_consensus_visualization()
    
    def consensus_reset_view(self):
        """Сброс вида консенсуса"""
        self.consensus_zoom = 1.0
        self.consensus_pan_x = 0
        self.consensus_pan_y = 0
        self.consensus_scale_var.set("1.0x")
        self.update_consensus_visualization()
    
    def consensus_start_pan(self, event):
        """Начало перемещения"""
        self.consensus_canvas.scan_mark(event.x, event.y)
    
    def consensus_pan(self, event):
        """Перемещение"""
        self.consensus_canvas.scan_dragto(event.x, event.y, gain=1)
    
    def consensus_on_mousewheel(self, event):
        """Масштабирование колесом мыши"""
        if event.delta > 0 or event.num == 4:
            self.consensus_zoom_in()
        else:
            self.consensus_zoom_out()
    
    def update_consensus_visualization(self):
        self.consensus_canvas.delete("all")
        
        if not self.system.consensus:
            return
        
        # Визуализация узлов с учетом zoom и pan
        node_status = self.system.consensus.get_node_status()
        base_width = 1000
        base_height = 600
        
        x_center = base_width / 2 + self.consensus_pan_x
        y_center = base_height / 2 + self.consensus_pan_y
        
        # Применяем масштабирование
        node_size = int(40 * self.consensus_zoom)
        text_size = int(12 * self.consensus_zoom)
        small_text_size = int(9 * self.consensus_zoom)
        
        # ЦБ в центре
        cb_node = self.system.consensus.nodes.get(self.system.central_bank.bank_id)
        if cb_node:
            is_failed = cb_node.node_id in self.system.failed_nodes
            color = "red" if cb_node.state.value == "Leader" and not is_failed else ("darkred" if is_failed else "lightblue")
            self.consensus_canvas.create_oval(
                x_center-node_size, y_center-node_size, 
                x_center+node_size, y_center+node_size, 
                fill=color, outline="black", width=int(3 * self.consensus_zoom), tags="node"
            )
            self.consensus_canvas.create_text(x_center, y_center, text="ЦБ", 
                                            font=("Arial", text_size, "bold"), tags="node")
            self.consensus_canvas.create_text(x_center, y_center+node_size+10, 
                                            text=cb_node.state.value, 
                                            font=("Arial", small_text_size), tags="node")
            if is_failed:
                self.consensus_canvas.create_text(x_center, y_center-node_size-15, 
                                                text="ОТКАЗ", 
                                                font=("Arial", small_text_size, "bold"), 
                                                fill="red", tags="node")
        
        # ФО вокруг по кругу
        bank_nodes = [n for n in self.system.consensus.nodes.values() if not n.is_central_bank]
        radius = min(base_width, base_height) / 3 * self.consensus_zoom
        
        for i, node in enumerate(bank_nodes):
            angle = (i * 2 * 3.14159) / len(bank_nodes) - 3.14159 / 2  # Начинаем сверху
            x = x_center + radius * (1.2 if len(bank_nodes) > 4 else 1.0) * (1 if i < len(bank_nodes)/2 else -1) * abs(3.14159/2 - abs(angle))
            y = y_center + radius * (1.2 if len(bank_nodes) > 4 else 1.0) * (1 if angle > 0 else -1) * abs(angle)
            
            is_failed = node.node_id in self.system.failed_nodes
            color = "green" if node.state.value == "Leader" and not is_failed else ("darkred" if is_failed else "lightgray")
            
            node_radius = int(30 * self.consensus_zoom)
            self.consensus_canvas.create_oval(x-node_radius, y-node_radius, x+node_radius, y+node_radius, 
                                             fill=color, outline="black", width=int(2 * self.consensus_zoom), tags="node")
            self.consensus_canvas.create_text(x, y, text=node.node_id[:8], 
                                            font=("Arial", int(8 * self.consensus_zoom)), tags="node")
            self.consensus_canvas.create_text(x, y+node_radius+10, text=node.state.value, 
                                            font=("Arial", int(7 * self.consensus_zoom)), tags="node")
            if is_failed:
                self.consensus_canvas.create_text(x, y-node_radius-15, text="ОТКАЗ", 
                                                font=("Arial", int(8 * self.consensus_zoom), "bold"), 
                                                fill="red", tags="node")
            
            # Линия связи с ЦБ
            if not is_failed and cb_node and cb_node.node_id not in self.system.failed_nodes:
                self.consensus_canvas.create_line(x_center, y_center, x, y, 
                                                 fill="gray", width=int(1 * self.consensus_zoom), 
                                                 dash=(5, 5), tags="connection")
        
        # Обновляем scrollregion
        self.consensus_canvas.configure(scrollregion=self.consensus_canvas.bbox("all"))
        
        # Обновление таблиц
        for item in self.tx_hash_tree.get_children():
            self.tx_hash_tree.delete(item)
        
        leader = self.system.consensus.get_leader()
        if leader:
            total_nodes = len(self.system.consensus.nodes)
            active_nodes = [n for n in self.system.consensus.nodes.values() 
                          if n.node_id not in self.system.failed_nodes 
                          and n.node_id not in self.system.recovering_nodes]
            active_count = len(active_nodes)
            
            for tx_hash_data in leader.transaction_hashes[-20:]:  # Последние 20
                quorum_str = f"{active_count}/{total_nodes}"
                self.tx_hash_tree.insert("", tk.END, values=(
                    tx_hash_data['hash'][:20] + "...",
                    tx_hash_data['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                    quorum_str
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
        
        canvas_width = self.blockchain_canvas.winfo_width() or 1000
        canvas_height = self.blockchain_canvas.winfo_height() or 500
        
        # Визуализация блоков с детальными связями родитель-наследник
        x_start = 50
        y_start = 80
        block_width = 160
        block_height = 120
        block_spacing = 180
        
        blocks = self.system.blockchain.chain
        if not blocks:
            return
        
        max_blocks = min(10, len(blocks))  # Показываем последние 10 блоков
        
        # Словарь для хранения позиций блоков
        block_positions = {}
        
        display_blocks = blocks[-max_blocks:] if len(blocks) > max_blocks else blocks
        start_index = max(0, len(blocks) - len(display_blocks))
        
        for i, block in enumerate(display_blocks):
            actual_index = start_index + i
            x = x_start + i * block_spacing
            y = y_start
            block_positions[block.block_id] = (x, y, block)
            
            # Определение цвета блока
            if block.block_id == "GENESIS":
                color = "gold"
            elif i == len(display_blocks) - 1:
                color = "lightgreen"  # Последний блок
            else:
                color = "lightblue"
            
            # Рамка блока
            self.blockchain_canvas.create_rectangle(x, y, x+block_width, y+block_height, 
                                                   fill=color, outline="black", width=3)
            
            # ID блока
            self.blockchain_canvas.create_text(x+block_width/2, y+15, text=block.block_id, 
                                              font=("Arial", 11, "bold"))
            
            # Индекс блока в цепочке
            self.blockchain_canvas.create_text(x+block_width/2, y+30, 
                                              text=f"#{actual_index}", 
                                              font=("Arial", 8, "italic"))
            
            # Количество транзакций
            self.blockchain_canvas.create_text(x+block_width/2, y+45, 
                                              text=f"Транзакций: {len(block.transactions)}", 
                                              font=("Arial", 9))
            
            # Хеш блока (первые 12 символов)
            self.blockchain_canvas.create_text(x+block_width/2, y+62, 
                                              text=f"Hash: {block.block_hash[:12]}...", 
                                              font=("Arial", 7))
            
            # Предыдущий хеш (первые 10 символов)
            prev_hash_short = block.previous_hash[:10] + "..." if len(block.previous_hash) > 10 else block.previous_hash
            self.blockchain_canvas.create_text(x+block_width/2, y+78, 
                                              text=f"Prev: {prev_hash_short}", 
                                              font=("Arial", 7))
            
            # Подписи
            self.blockchain_canvas.create_text(x+block_width/2, y+95, 
                                              text=f"Подписей: {len(block.signatures)}", 
                                              font=("Arial", 8))
            
            # Узел создатель
            node_text = block.node_id[:8] if block.node_id else "N/A"
            self.blockchain_canvas.create_text(x+block_width/2, y+110, 
                                              text=f"Узел: {node_text}", 
                                              font=("Arial", 7))
            
            # Связь с родительским блоком (предыдущим)
            if i > 0 and actual_index > 0 and actual_index - 1 < len(blocks):
                prev_block = blocks[actual_index - 1]
                prev_x = x_start + (i-1) * block_spacing + block_width
                current_x = x
                mid_y = y + block_height / 2
                
                # Толстая стрелка связи родитель-наследник
                arrow_length = current_x - prev_x
                arrow_start_x = prev_x
                arrow_end_x = current_x
                
                # Основная линия связи
                self.blockchain_canvas.create_line(arrow_start_x, mid_y, arrow_end_x, mid_y, 
                                                   arrow=tk.LAST, width=4, fill="darkblue", 
                                                   arrowshape=(10, 12, 3))
                
                # Дополнительная линия для визуализации связи
                self.blockchain_canvas.create_line(arrow_start_x, mid_y-2, arrow_end_x, mid_y-2, 
                                                   width=2, fill="blue", dash=(3, 2))
                
                # Текст связи с информацией
                link_text = f"← Родитель: {prev_block.block_id}"
                self.blockchain_canvas.create_text((arrow_start_x+arrow_end_x)/2, mid_y-25, 
                                                  text=link_text, 
                                                  font=("Arial", 9, "bold"), fill="darkblue")
                
                # Информация о связи
                connection_info = f"Prev Hash: {prev_block.block_hash[:8]}..."
                self.blockchain_canvas.create_text((arrow_start_x+arrow_end_x)/2, mid_y+25, 
                                                  text=connection_info, 
                                                  font=("Arial", 7), fill="darkgreen")
        
        # Заголовок
        self.blockchain_canvas.create_text(canvas_width/2, 30, 
                                          text="Распределенный реестр: Связи блоков (Родитель → Наследник)", 
                                          font=("Arial", 14, "bold"))
        
        # Легенда
        legend_y = y_start + block_height + 20
        self.blockchain_canvas.create_text(100, legend_y, text="Легенда:", 
                                          font=("Arial", 10, "bold"))
        self.blockchain_canvas.create_rectangle(100, legend_y+15, 120, legend_y+25, fill="gold", outline="black")
        self.blockchain_canvas.create_text(140, legend_y+20, text="Генезис-блок", font=("Arial", 8))
        self.blockchain_canvas.create_rectangle(220, legend_y+15, 240, legend_y+25, fill="lightblue", outline="black")
        self.blockchain_canvas.create_text(260, legend_y+20, text="Обычный блок", font=("Arial", 8))
        self.blockchain_canvas.create_rectangle(360, legend_y+15, 380, legend_y+25, fill="lightgreen", outline="black")
        self.blockchain_canvas.create_text(400, legend_y+20, text="Последний блок", font=("Arial", 8))
        self.blockchain_canvas.create_line(500, legend_y+20, 550, legend_y+20, arrow=tk.LAST, width=3, fill="darkblue")
        self.blockchain_canvas.create_text(570, legend_y+20, text="Связь родитель→наследник", font=("Arial", 8))
        
        # Распределение по узлам
        y_nodes = legend_y + 50
        self.blockchain_canvas.create_text(canvas_width/2, y_nodes, 
                                          text="Распределение блоков по узлам сети", 
                                          font=("Arial", 12, "bold"))
        
        # Визуализация узлов с блоками
        node_x_start = 50
        node_y = y_nodes + 30
        node_spacing = 180
        
        for idx, (node_id, node_blocks) in enumerate(list(self.system.blockchain.nodes.items())[:5]):
            x_node = node_x_start + (idx % 3) * node_spacing
            y_node_pos = node_y + (idx // 3) * 60
            
            # Узел
            node_color = "orange" if node_id == self.system.central_bank.bank_id else "lightgreen"
            self.blockchain_canvas.create_oval(x_node-25, y_node_pos-25, x_node+25, y_node_pos+25, 
                                             fill=node_color, outline="black", width=2)
            self.blockchain_canvas.create_text(x_node, y_node_pos, text=node_id[:6], 
                                              font=("Arial", 8, "bold"))
            
            # Количество блоков
            self.blockchain_canvas.create_text(x_node, y_node_pos+35, 
                                              text=f"{len(node_blocks)} блоков", 
                                              font=("Arial", 8))
        
        # Обновление таблицы блоков с информацией о связях
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)
        
        if not blocks:
            return
        
        # Берем последние 20 блоков или все, если их меньше
        display_blocks = blocks[-20:] if len(blocks) > 20 else blocks
        start_idx = max(0, len(blocks) - len(display_blocks))
        
        for idx, block in enumerate(display_blocks):
            actual_idx = start_idx + idx
            # Найти родительский блок
            if actual_idx == 0:
                parent_id = "GENESIS"
                connection_status = "✓ Связан"
            elif actual_idx > 0 and actual_idx - 1 < len(blocks):
                parent_id = blocks[actual_idx - 1].block_id
                prev_block = blocks[actual_idx - 1]
                connection_status = "✓ Связан" if block.previous_hash == prev_block.block_hash else "✗ Разрыв"
            else:
                parent_id = "N/A"
                connection_status = "✗ Разрыв"
            
            self.blocks_tree.insert("", tk.END, values=(
                block.block_id,
                parent_id,
                block.previous_hash[:20] + "...",
                block.block_hash[:20] + "...",
                block.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                block.node_id or "",
                len(block.transactions),
                connection_status
            ))
    
    def update_metrics(self):
        try:
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
                # График 1: Количество транзакций (улучшенный)
                ax1 = self.metrics_figure.add_subplot(2, 2, 1)
                total_tx = metrics.get('total_transactions', 0)
                tx_times = self.system.transaction_processor.metrics.get('tx_creation_times', [])
                
                if tx_times and len(tx_times) > 0:
                    # Берем все точки для визуализации, но ограничиваем для производительности
                    display_tx = tx_times[-500:] if len(tx_times) > 500 else tx_times
                    # Если много данных, берем каждую N-ю точку
                    if len(display_tx) > 200:
                        step = len(display_tx) // 200
                        display_tx = display_tx[::step]
                    
                    x_data = range(len(display_tx))
                    ax1.plot(x_data, display_tx, 'b-', linewidth=1.5, alpha=0.7)
                    ax1.set_title(f'Время создания транзакций (всего: {total_tx})')
                    ax1.set_xlabel('Номер транзакции')
                    ax1.set_ylabel('Время (мс)')
                    ax1.grid(True, alpha=0.3)
                    if len(display_tx) > 0:
                        max_val = max(display_tx) * 1.2 if max(display_tx) > 0 else 1000
                        min_val = min(display_tx) * 0.8 if min(display_tx) > 0 else 0
                        ax1.set_ylim(max(0, min_val), max(max_val, 100))
                        # Добавляем среднюю линию
                        avg_time = sum(display_tx) / len(display_tx)
                        ax1.axhline(y=avg_time, color='r', linestyle='--', linewidth=1, label=f'Среднее: {avg_time:.2f} мс')
                        ax1.legend(fontsize=8)
                else:
                    ax1.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax1.transAxes)
                    ax1.set_title('Время создания транзакций')
                    ax1.set_xlabel('Транзакция')
                    ax1.set_ylabel('Время (мс)')
                
                # График 2: Время создания блоков (улучшенный)
                ax2 = self.metrics_figure.add_subplot(2, 2, 2)
                block_times = self.system.blockchain.metrics.get('block_creation_times', [])
                if block_times and len(block_times) > 0:
                    x_data = range(len(block_times))
                    ax2.plot(x_data, block_times, 'g-', linewidth=2, marker='o', markersize=3, alpha=0.7)
                    ax2.set_title(f'Время создания блоков (всего: {len(block_times)})')
                    ax2.set_xlabel('Номер блока')
                    ax2.set_ylabel('Время (мс)')
                    ax2.grid(True, alpha=0.3)
                    max_val = max(block_times) * 1.2 if max(block_times) > 0 else 2000
                    min_val = min(block_times) * 0.8 if min(block_times) > 0 else 0
                    ax2.set_ylim(max(0, min_val), max(max_val, 500))
                    # Средняя линия
                    avg_time = sum(block_times) / len(block_times)
                    ax2.axhline(y=avg_time, color='r', linestyle='--', linewidth=1, label=f'Среднее: {avg_time:.2f} мс')
                    ax2.legend(fontsize=8)
                else:
                    ax2.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax2.transAxes)
                    ax2.set_title('Время создания блоков')
                    ax2.set_xlabel('Блок')
                    ax2.set_ylabel('Время (мс)')
                
                # График 3: Время записи в реестр (улучшенный)
                ax3 = self.metrics_figure.add_subplot(2, 2, 3)
                registry_times = self.system.blockchain.metrics.get('block_registry_times', [])
                if registry_times and len(registry_times) > 0:
                    x_data = range(len(registry_times))
                    ax3.plot(x_data, registry_times, 'r-', linewidth=2, marker='s', markersize=3, alpha=0.7)
                    ax3.set_title(f'Время записи блоков в реестр (всего: {len(registry_times)})')
                    ax3.set_xlabel('Номер блока')
                    ax3.set_ylabel('Время (мс)')
                    ax3.grid(True, alpha=0.3)
                    max_val = max(registry_times) * 1.2 if max(registry_times) > 0 else 1000
                    min_val = min(registry_times) * 0.8 if min(registry_times) > 0 else 0
                    ax3.set_ylim(max(0, min_val), max(max_val, 200))
                    # Средняя линия
                    avg_time = sum(registry_times) / len(registry_times)
                    ax3.axhline(y=avg_time, color='b', linestyle='--', linewidth=1, label=f'Среднее: {avg_time:.2f} мс')
                    ax3.legend(fontsize=8)
                else:
                    ax3.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax3.transAxes)
                    ax3.set_title('Время записи блоков в реестр')
                    ax3.set_xlabel('Блок')
                    ax3.set_ylabel('Время (мс)')
                
                # График 4: Общая нагрузка и TPS (улучшенный)
                ax4 = self.metrics_figure.add_subplot(2, 2, 4)
                tps = metrics.get('tps', 0)
                blocks_count = len(self.system.blockchain.chain) if self.system.blockchain else 0
                
                # График нагрузки с правильным масштабированием
                categories = ['Транзакции', 'Блоки']
                values = [total_tx, blocks_count]
                colors = ['blue', 'green']
                
                # Нормализуем значения для визуализации
                if total_tx > 0 or blocks_count > 0:
                    max_val = max(values) if values else 1
                    normalized_values = [v / max_val * 100 if max_val > 0 else 0 for v in values]
                    
                    bars = ax4.bar(categories, normalized_values, color=colors, alpha=0.7)
                    ax4.set_title(f'Общая нагрузка системы (нормализовано)')
                    ax4.set_ylabel('Нормализованное значение (%)')
                    ax4.grid(True, alpha=0.3, axis='y')
                    ax4.set_ylim(0, 110)
                    
                    # Добавляем реальные значения на столбцы
                    for bar, val, cat in zip(bars, normalized_values, categories):
                        height = bar.get_height()
                        real_val = values[categories.index(cat)]
                        label = f'{int(real_val)}'
                        ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                                label, ha='center', va='bottom', fontsize=9)
                    
                    # TPS отдельно
                    if tps > 0:
                        ax4_twin = ax4.twinx()
                        ax4_twin.bar(['TPS'], [min(tps, 100)], color='orange', alpha=0.7, width=0.3)
                        ax4_twin.set_ylabel('TPS', color='orange')
                        ax4_twin.set_ylim(0, max(tps * 1.1, 100))
                        ax4_twin.tick_params(axis='y', labelcolor='orange')
                        ax4_twin.text(0, min(tps, 100) + 2, f'{tps:.1f}', ha='center', va='bottom', fontsize=9)
                else:
                    # Если нет данных, показываем пустой график
                    ax4.text(0.5, 0.5, 'Нет данных', ha='center', va='center', transform=ax4.transAxes)
                    ax4.set_title('Общая нагрузка системы')
            
            self.metrics_figure.tight_layout()
            self.metrics_canvas.draw()
        except Exception as e:
            print(f"Ошибка обновления метрик: {e}")
            import traceback
            traceback.print_exc()
    
    def update_cb_tables(self):
        """Обновление таблиц ЦБ"""
        try:
            # Обновление запросов на эмиссию
            for item in self.cb_emission_tree.get_children():
                self.cb_emission_tree.delete(item)
            
            status_map = {
                'pending': 'В обработке',
                'approved': 'Одобрено',
                'rejected': 'Отклонено'
            }
            emission_records = self.system.database.get_recent_emission_requests(limit=40)
            for req in emission_records:
                self.cb_emission_tree.insert("", tk.END, values=(
                    req.bank_id,
                    f"{req.amount:.2f}",
                    req.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    status_map.get(req.status, req.status)
                ))
            
            # Обновление транзакций
            for item in self.cb_tx_tree.get_children():
                self.cb_tx_tree.delete(item)
            
            if self.system.transaction_processor:
                for tx in self.system.transaction_processor.transactions[-20:]:
                    self.cb_tx_tree.insert("", tk.END, values=(
                        tx.transaction_id[:12],
                        tx.sender_id[:12],
                        tx.receiver_id[:12],
                        f"{tx.amount:.2f}",
                        tx.transaction_type.value,
                        tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        tx.status.value
                    ))
            
            # Обновление формирования блоков
            for item in self.cb_block_formation_tree.get_children():
                self.cb_block_formation_tree.delete(item)
            
            for event in self.system.block_formation_events[-20:]:
                self.cb_block_formation_tree.insert("", tk.END, values=(
                    event.get('timestamp', datetime.now()).strftime("%Y-%m-%d %H:%M:%S") if isinstance(event.get('timestamp'), datetime) else str(event.get('timestamp', '')),
                    event.get('stage', ''),
                    event.get('pending_transactions', 0),
                    event.get('block_id', '')
                ))
            
            # Обновление подписания блоков
            for item in self.cb_signing_tree.get_children():
                self.cb_signing_tree.delete(item)
            
            for event in self.system.block_signing_events[-20:]:
                self.cb_signing_tree.insert("", tk.END, values=(
                    event.get('timestamp', datetime.now()).strftime("%Y-%m-%d %H:%M:%S") if isinstance(event.get('timestamp'), datetime) else str(event.get('timestamp', '')),
                    event.get('block_id', ''),
                    event.get('signatures_count', 0),
                    'Подписан'
                ))
            
            # Обновление записи в реестр
            for item in self.cb_registry_tree.get_children():
                self.cb_registry_tree.delete(item)
            
            registry_events = self.system.database.get_block_registry_events(limit=40)
            for event in registry_events:
                details = f"{event.status}" if not event.details else f"{event.status} | {event.details}"
                self.cb_registry_tree.insert("", tk.END, values=(
                    event.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    event.block_id,
                    event.node_id or "—",
                    details
                ))
        except Exception as e:
            print(f"Ошибка обновления таблиц ЦБ: {e}")
    
    def simulate_incident(self):
        """Симуляция инцидента"""
        incident_type_full = self.incident_type_var.get()
        if not incident_type_full:
            messagebox.showwarning("Предупреждение", "Выберите тип инцидента")
            return
        
        # Извлекаем тип инцидента из строки (до первого пробела или дефиса)
        incident_type = incident_type_full.split()[0] if incident_type_full else ""
        
        result = self.system.simulate_incident(incident_type)
        
        result_text = f"\n{'='*60}\n"
        result_text += f"ИНЦИДЕНТ: {result.get('incident_type', 'unknown')}\n"
        result_text += f"Время начала: {result.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}\n"
        result_text += f"{'='*60}\n\n"
        
        # Показываем поэтапное восстановление
        stages = result.get('stages', [])
        if stages:
            result_text += "ЭТАПЫ ИНЦИДЕНТА И ВОССТАНОВЛЕНИЯ:\n"
            result_text += "-" * 60 + "\n"
            stage_counter = 1
            for stage in stages:
                stage_name = stage.get('stage', '')
                message = stage.get('message', '')
                timestamp = stage.get('timestamp', datetime.now())
                if isinstance(timestamp, datetime):
                    time_str = timestamp.strftime('%H:%M:%S')
                else:
                    time_str = str(timestamp)
                
                result_text += f"\n[{stage_counter}] {time_str} - {stage_name.upper()}\n"
                result_text += f"    {message}\n"
                stage_counter += 1
        
        # Находим ID узлов, которые отказали в этом инциденте
        failed_node_ids = []
        for stage in stages:
            msg = stage.get('message', '')
            if 'отказал' in msg:
                # Извлекаем ID узла из сообщения
                if 'ЦБ' in msg or self.system.central_bank.bank_id in msg:
                    failed_node_ids.append(self.system.central_bank.bank_id)
                else:
                    # Пытаемся извлечь ID из сообщения
                    parts = msg.split()
                    for part in parts:
                        if part in self.system.consensus.nodes:
                            failed_node_ids.append(part)
                            break
        
        # Добавляем события восстановления для этих узлов (если они уже произошли)
        if failed_node_ids:
            for node_id in failed_node_ids:
                # Ищем события восстановления для этого узла после начала инцидента
                recovery_events_for_node = [e for e in self.system.incident_recovery_events 
                                          if e.get('node_id') == node_id 
                                          and isinstance(e.get('timestamp'), datetime)
                                          and isinstance(result.get('timestamp'), datetime)
                                          and e.get('timestamp') >= result.get('timestamp')]
                for event in recovery_events_for_node:
                    stage_name = event.get('stage', '')
                    message = event.get('message', '')
                    timestamp = event.get('timestamp', datetime.now())
                    if isinstance(timestamp, datetime):
                        time_str = timestamp.strftime('%H:%M:%S')
                    else:
                        time_str = str(timestamp)
                    result_text += f"\n[{stage_counter}] {time_str} - {stage_name.upper()}\n"
                    result_text += f"    {message}\n"
                    stage_counter += 1
        
        result_text += f"\n{'='*60}\n"
        result_text += f"Кворум достигнут: {'ДА' if result.get('quorum_reached', False) else 'НЕТ'}\n"
        if result.get('recovery_time', 0) > 0:
            result_text += f"Время восстановления: {result.get('recovery_time', 0):.2f} с\n"
        if result.get('message'):
            result_text += f"Сообщение: {result.get('message')}\n"
        result_text += f"{'='*60}\n\n"
        
        self.incidents_results.insert(tk.END, result_text)
        self.incidents_results.see(tk.END)
    
    def on_node_recovered(self, event):
        """Обработка события восстановления узла"""
        message = event.get('message', '')
        timestamp = event.get('timestamp', datetime.now())
        time_str = timestamp.strftime('%H:%M:%S') if isinstance(timestamp, datetime) else str(timestamp)
        
        recovery_text = f"\n[{time_str}] ВОССТАНОВЛЕНИЕ УЗЛА\n"
        recovery_text += f"    {message}\n"
        recovery_text += "-" * 60 + "\n"
        
        self.incidents_results.insert(tk.END, recovery_text)
        self.incidents_results.see(tk.END)
    
    def update_bank_data(self):
        """Обновление данных выбранного банка"""
        bank_id = self.bank_select_var.get()
        if not bank_id:
            return
        
        # Обновление транзакций
        for item in self.bank_tx_tree.get_children():
            self.bank_tx_tree.delete(item)
        
        if self.system.transaction_processor:
            for tx in self.system.transaction_processor.transactions:
                if tx.bank_id == bank_id:
                    self.bank_tx_tree.insert("", tk.END, values=(
                        tx.transaction_id[:12],
                        tx.sender_id[:12],
                        tx.receiver_id[:12],
                        f"{tx.amount:.2f}",
                        tx.transaction_type.value,
                        tx.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        tx.status.value
                    ))
        
        # Обновление голосований за блоки
        for item in self.bank_voting_tree.get_children():
            self.bank_voting_tree.delete(item)
        
        if self.system.blockchain:
            for block in self.system.blockchain.chain:
                # Симулируем голосование
                vote_status = "За" if bank_id in [b for b in self.system.user_manager.banks.keys()] else "Против"
                voting_result = "Принято" if len(block.signatures) > 2 else "Ожидает"
                
                self.bank_voting_tree.insert("", tk.END, values=(
                    block.block_id,
                    block.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    vote_status,
                    voting_result,
                    f"{len(block.signatures)} подписей"
                ))
        
        # Обновление блоков в ФО
        for item in self.bank_blocks_tree.get_children():
            self.bank_blocks_tree.delete(item)
        
        if self.system.blockchain and bank_id in self.system.blockchain.nodes:
            node_blocks = self.system.blockchain.nodes[bank_id]
            if node_blocks:
                display_blocks = node_blocks[-20:] if len(node_blocks) > 20 else node_blocks
                for block in display_blocks:
                    self.bank_blocks_tree.insert("", tk.END, values=(
                        block.block_id,
                        block.block_hash[:20] + "...",
                        block.previous_hash[:20] + "...",
                        len(block.transactions),
                        block.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "Да" if len(block.signatures) > 0 else "Нет"
                    ))
    
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
    
    def on_emission_request(self, request):
        pass  # Обновление через таймер
    
    def on_emission_approved(self, data):
        pass  # Обновление через таймер
    
    def on_block_formation_started(self, event):
        pass  # Обновление через таймер
    
    def on_block_signed(self, event):
        pass  # Обновление через таймер
    
    def on_block_registered(self, event):
        pass  # Обновление через таймер
    
    def on_node_failed(self, data):
        pass  # Обновление через таймер
    
    def on_incident_handled(self, result):
        pass  # Обновление через таймер
    
    def update_timer(self):
        """Таймер обновления данных"""
        try:
            # Обновление таймера симуляции
            if self.system.simulation_running:
                elapsed = self.system.get_simulation_elapsed_time()
                remaining = self.system.get_simulation_time_remaining()
                total = self.system.simulation_duration
                
                elapsed_min = int(elapsed // 60)
                elapsed_sec = int(elapsed % 60)
                total_min = int(total // 60)
                total_sec = int(total % 60)
                
                self.timer_label.config(
                    text=f"Время: {elapsed_min:02d}:{elapsed_sec:02d} / {total_min:02d}:{total_sec:02d}"
                )
                progress = (elapsed / total * 100) if total > 0 else 0
                self.progress_var.set(min(100, progress))
            
            # Обновление только если симуляция не остановлена
            if self.system.simulation_running or not hasattr(self, '_simulation_was_running'):
                self._simulation_was_running = self.system.simulation_running
                self.update_users_table()
                self.update_transactions_table()
                self.update_offline_transactions_table()
                self.update_smart_contracts_table()
                self.update_consensus_visualization()
                self.update_blockchain_visualization()
                self.update_cb_tables()
                self.update_user_list()
                self.update_bank_list()
                # Обновление данных банка если выбран
                if self.bank_select_var.get():
                    self.update_bank_data()
                # Обновление метрик каждые 5 секунд
                if not hasattr(self, '_last_metrics_update'):
                    self._last_metrics_update = 0
                import time
                current_time = time.time()
                if current_time - self._last_metrics_update >= 5:
                    try:
                        self.update_metrics()
                        self._last_metrics_update = current_time
                    except Exception as e:
                        print(f"Ошибка обновления метрик: {e}")
        except Exception as e:
            print(f"Ошибка обновления: {e}")
            import traceback
            traceback.print_exc()
        
        # Продолжаем обновление независимо от ошибок
        self.root.after(1000, self.update_timer)  # Обновление каждую секунду


def main():
    root = tk.Tk()
    app = DigitalRubleGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

