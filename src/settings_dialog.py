"""Settings dialog for application configuration."""

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """Settings dialog for configuring the application."""

    def __init__(self, settings: QSettings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.custom_paths: list[str] = []

        self.setWindowTitle("設定")
        self.setMinimumSize(500, 400)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Tab widget
        tabs = QTabWidget()

        # SimBrief tab
        simbrief_tab = self._create_simbrief_tab()
        tabs.addTab(simbrief_tab, "SimBrief")

        # Paths tab
        paths_tab = self._create_paths_tab()
        tabs.addTab(paths_tab, "フォルダ")

        # Display tab
        display_tab = self._create_display_tab()
        tabs.addTab(display_tab, "表示")

        layout.addWidget(tabs)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._on_apply)
        layout.addWidget(button_box)

    def _create_simbrief_tab(self) -> QWidget:
        """Create the SimBrief settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # SimBrief account group
        account_group = QGroupBox("SimBriefアカウント")
        account_layout = QFormLayout(account_group)

        self.pilot_id_edit = QLineEdit()
        self.pilot_id_edit.setPlaceholderText("Pilot ID または ユーザー名")
        account_layout.addRow("Pilot ID:", self.pilot_id_edit)

        # Help text
        help_label = QLabel(
            "SimBrief Pilot IDは、SimBrief.comの\n"
            "Account Settings → Pilot ID で確認できます。"
        )
        help_label.setStyleSheet("color: #888; font-size: 11px;")
        account_layout.addRow("", help_label)

        layout.addWidget(account_group)

        # Options group
        options_group = QGroupBox("オプション")
        options_layout = QFormLayout(options_group)

        self.auto_fetch_check = QCheckBox("起動時に最新のOFPを自動取得")
        options_layout.addRow("", self.auto_fetch_check)

        layout.addWidget(options_group)

        # Test button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_btn = QPushButton("接続テスト")
        self.test_btn.clicked.connect(self._test_simbrief_connection)
        test_layout.addWidget(self.test_btn)
        layout.addLayout(test_layout)

        layout.addStretch()
        return widget

    def _create_paths_tab(self) -> QWidget:
        """Create the custom paths settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Custom paths group
        paths_group = QGroupBox("カスタムフライトプランフォルダ")
        paths_layout = QVBoxLayout(paths_group)

        self.paths_list = QListWidget()
        paths_layout.addWidget(self.paths_list)

        btn_layout = QHBoxLayout()
        self.add_path_btn = QPushButton("追加...")
        self.add_path_btn.clicked.connect(self._add_custom_path)
        btn_layout.addWidget(self.add_path_btn)

        self.remove_path_btn = QPushButton("削除")
        self.remove_path_btn.clicked.connect(self._remove_custom_path)
        btn_layout.addWidget(self.remove_path_btn)

        btn_layout.addStretch()
        paths_layout.addLayout(btn_layout)

        layout.addWidget(paths_group)

        # NavData group
        navdata_group = QGroupBox("ナビゲーションデータ")
        navdata_layout = QFormLayout(navdata_group)

        self.navdata_path_edit = QLineEdit()
        self.navdata_path_edit.setPlaceholderText("X-Plane earth_nav.dat へのパス (オプション)")
        navdata_layout.addRow("NAVDATAファイル:", self.navdata_path_edit)

        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self._browse_navdata)
        navdata_layout.addRow("", browse_btn)

        layout.addWidget(navdata_group)

        layout.addStretch()
        return widget

    def _create_display_tab(self) -> QWidget:
        """Create the display settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Speed settings
        speed_group = QGroupBox("速度設定")
        speed_layout = QFormLayout(speed_group)

        self.default_speed_spin = QSpinBox()
        self.default_speed_spin.setRange(100, 600)
        self.default_speed_spin.setSuffix(" kts")
        speed_layout.addRow("デフォルト巡航速度:", self.default_speed_spin)

        layout.addWidget(speed_group)

        # Map settings
        map_group = QGroupBox("地図設定")
        map_layout = QFormLayout(map_group)

        self.show_labels_check = QCheckBox("ウェイポイントラベルを表示")
        self.show_labels_check.setChecked(True)
        map_layout.addRow("", self.show_labels_check)

        self.show_airways_check = QCheckBox("エアウェイ名を表示")
        self.show_airways_check.setChecked(True)
        map_layout.addRow("", self.show_airways_check)

        layout.addWidget(map_group)

        # Units
        units_group = QGroupBox("単位")
        units_layout = QFormLayout(units_group)

        self.use_metric_check = QCheckBox("メートル法を使用 (km, kg)")
        units_layout.addRow("", self.use_metric_check)

        layout.addWidget(units_group)

        layout.addStretch()
        return widget

    def _load_settings(self):
        """Load settings from QSettings."""
        # SimBrief
        self.pilot_id_edit.setText(self.settings.value("simbrief/pilot_id", ""))
        self.auto_fetch_check.setChecked(
            self.settings.value("simbrief/auto_fetch", False, type=bool)
        )

        # Paths
        self.custom_paths = self.settings.value("custom_paths", []) or []
        self.paths_list.clear()
        for path in self.custom_paths:
            self.paths_list.addItem(path)

        self.navdata_path_edit.setText(
            self.settings.value("navdata/path", "")
        )

        # Display
        self.default_speed_spin.setValue(
            self.settings.value("cruise_speed", 450, type=int)
        )
        self.show_labels_check.setChecked(
            self.settings.value("display/show_labels", True, type=bool)
        )
        self.show_airways_check.setChecked(
            self.settings.value("display/show_airways", True, type=bool)
        )
        self.use_metric_check.setChecked(
            self.settings.value("display/use_metric", False, type=bool)
        )

    def _save_settings(self):
        """Save settings to QSettings."""
        # SimBrief
        self.settings.setValue("simbrief/pilot_id", self.pilot_id_edit.text().strip())
        self.settings.setValue("simbrief/auto_fetch", self.auto_fetch_check.isChecked())

        # Paths
        self.custom_paths = []
        for i in range(self.paths_list.count()):
            self.custom_paths.append(self.paths_list.item(i).text())
        self.settings.setValue("custom_paths", self.custom_paths)

        self.settings.setValue("navdata/path", self.navdata_path_edit.text().strip())

        # Display
        self.settings.setValue("cruise_speed", self.default_speed_spin.value())
        self.settings.setValue("display/show_labels", self.show_labels_check.isChecked())
        self.settings.setValue("display/show_airways", self.show_airways_check.isChecked())
        self.settings.setValue("display/use_metric", self.use_metric_check.isChecked())

    def _test_simbrief_connection(self):
        """Test SimBrief connection."""
        pilot_id = self.pilot_id_edit.text().strip()
        if not pilot_id:
            QMessageBox.warning(self, "エラー", "Pilot IDを入力してください。")
            return

        self.test_btn.setEnabled(False)
        self.test_btn.setText("接続中...")

        try:
            from .simbrief import SimBriefClient
            client = SimBriefClient(pilot_id)
            ofp = client.fetch_latest_ofp()

            if ofp:
                QMessageBox.information(
                    self,
                    "接続成功",
                    f"SimBriefに接続しました。\n\n"
                    f"最新のフライトプラン:\n"
                    f"便名: {ofp.flight_number}\n"
                    f"ルート: {ofp.departure_icao} → {ofp.arrival_icao}\n"
                    f"機材: {ofp.aircraft_name}"
                )
            else:
                reason = client.last_error or "SimBriefに接続できませんでした。"
                QMessageBox.warning(self, "接続失敗", reason)
        except Exception as e:
            QMessageBox.critical(
                self,
                "エラー",
                f"接続中にエラーが発生しました:\n{str(e)}"
            )
        finally:
            self.test_btn.setEnabled(True)
            self.test_btn.setText("接続テスト")

    def _add_custom_path(self):
        """Add a custom path."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "フライトプランフォルダを選択",
            ""
        )
        if folder:
            # Check if already exists
            for i in range(self.paths_list.count()):
                if self.paths_list.item(i).text() == folder:
                    return

            self.paths_list.addItem(folder)

    def _remove_custom_path(self):
        """Remove selected custom path."""
        current = self.paths_list.currentRow()
        if current >= 0:
            self.paths_list.takeItem(current)

    def _browse_navdata(self):
        """Browse for navdata file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "ナビゲーションデータファイルを選択",
            "",
            "DAT Files (*.dat);;All Files (*.*)"
        )
        if file_path:
            self.navdata_path_edit.setText(file_path)

    def _on_apply(self):
        """Handle Apply button click."""
        self._save_settings()

    def _on_accept(self):
        """Handle OK button click."""
        self._save_settings()
        self.accept()

    def get_custom_paths(self) -> list[str]:
        """Get the list of custom paths."""
        return self.custom_paths

    def get_pilot_id(self) -> str:
        """Get the SimBrief pilot ID."""
        return self.pilot_id_edit.text().strip()
