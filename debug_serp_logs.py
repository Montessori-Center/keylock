#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для замены CompetitorsView.jsx и CompetitorsTable.jsx
Запускать из корневой директории проекта: python replace_competitors_view.py
"""

import os
from pathlib import Path

# Полный исправленный код CompetitorsView.jsx
COMPETITORS_VIEW_CONTENT = """// frontend/src/components/CompetitorsView.jsx
import React, { useState, useEffect } from 'react';
import CompetitorsTable from './CompetitorsTable';
import AddCompetitorModal from './Modals/AddCompetitorModal';
import ChangeFieldCompetitorModal from './Modals/ChangeFieldCompetitorModal';
import ApplyFiltersModal from './Modals/ApplyFiltersModal';
import axios from 'axios';
import { toast } from 'react-toastify';

// Создаём axios instance для API запросов
const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json'
  }
});

const CompetitorsView = ({ onClose }) => {
  const [competitors, setCompetitors] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  
  // Модальные окна
  const [showAddModal, setShowAddModal] = useState(false);
  const [showChangeFieldModal, setShowChangeFieldModal] = useState(false);
  const [showFiltersModal, setShowFiltersModal] = useState(false);

  // Загрузка данных при монтировании
  useEffect(() => {
    loadCompetitors();
    loadStats();
  }, []);

  const loadCompetitors = async () => {
    setLoading(true);
    try {
      const response = await apiClient.get('/api/competitors/list');
      if (response.data.success) {
        setCompetitors(response.data.competitors || []);
      } else {
        toast.error('Ошибка загрузки конкурентов');
      }
    } catch (error) {
      console.error('Error loading competitors:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiClient.get('/api/competitors/stats');
      if (response.data.success) {
        setStats(response.data.stats);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const handleAdd = async (competitorData) => {
    try {
      const response = await apiClient.post('/api/competitors/add', competitorData);
      if (response.data.success) {
        toast.success('Конкурент добавлен');
        loadCompetitors();
        loadStats();
      } else {
        throw new Error(response.data.error || 'Ошибка добавления');
      }
    } catch (error) {
      throw error;
    }
  };

  const handleDataChange = async (id, field, value) => {
    try {
      const response = await apiClient.post('/api/competitors/update', {
        id,
        field,
        value
      });
      
      if (response.data.success) {
        toast.success('Данные обновлены');
        loadCompetitors();
      } else {
        toast.error(response.data.error || 'Ошибка обновления');
      }
    } catch (error) {
      console.error('Error updating competitor:', error);
      toast.error('Ошибка при сохранении');
    }
  };

  const handleDelete = async () => {
    if (selectedIds.length === 0) {
      toast.warning('Выберите записи для удаления');
      return;
    }

    if (!window.confirm(`Удалить выбранные записи (${selectedIds.length})?`)) {
      return;
    }

    try {
      const response = await apiClient.post('/api/competitors/delete', {
        ids: selectedIds
      });

      if (response.data.success) {
        toast.success(response.data.message);
        setSelectedIds([]);
        loadCompetitors();
        loadStats();
      } else {
        toast.error(response.data.error || 'Ошибка удаления');
      }
    } catch (error) {
      console.error('Error deleting competitors:', error);
      toast.error('Ошибка при удалении');
    }
  };

  const handleCopyDomain = () => {
    if (selectedIds.length === 0) {
      toast.warning('Выберите записи');
      return;
    }

    // Находим выбранных конкурентов и копируем их домены
    const selectedCompetitors = competitors.filter(c => selectedIds.includes(c.id));
    const domains = selectedCompetitors.map(c => c.domain).join('\\n');
    
    navigator.clipboard.writeText(domains).then(() => {
      toast.success(`Скопировано доменов: ${selectedIds.length}`);
    }).catch(err => {
      console.error('Error copying:', err);
      toast.error('Ошибка копирования');
    });
  };

  const handleChangeField = async (field, value) => {
    if (selectedIds.length === 0) {
      toast.warning('Выберите записи');
      return;
    }

    try {
      // Обновляем каждую выбранную запись
      const promises = selectedIds.map(id => 
        apiClient.post('/api/competitors/update', { id, field, value })
      );

      await Promise.all(promises);
      
      toast.success(`Обновлено записей: ${selectedIds.length}`);
      loadCompetitors();
    } catch (error) {
      console.error('Error updating field:', error);
      toast.error('Ошибка при обновлении');
    }
  };

  const handleUnselectAll = () => {
    setSelectedIds([]);
  };

  return (
    <div className="competitors-view">
      {/* Заголовок со статистикой */}
      <div className="competitors-header">
        <div>
          <h2>Школы-конкуренты</h2>
          {stats && (
            <div className="competitors-stats">
              <div className="stat-item">
                <span className="stat-label">Всего</span>
                <span className="stat-value">{stats.total || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Школы</span>
                <span className="stat-value">{stats.schools || 0}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Базы репетиторов</span>
                <span className="stat-value">{stats.tutor_bases || 0}</span>
              </div>
            </div>
          )}
        </div>
        <button className="btn btn-secondary" onClick={onClose}>
          Закрыть
        </button>
      </div>

      {/* Контент с правильной структурой */}
      <div className="competitors-content">
        {/* Кнопки действий */}
        <div className="competitors-actions action-buttons">
          <button 
            className="btn btn-purple" 
            onClick={() => setShowAddModal(true)}
          >
            Добавить новый сайт
          </button>
          <button 
            className="btn btn-blue" 
            onClick={() => setShowFiltersModal(true)}
          >
            Применить фильтры
          </button>
        </div>

        {/* Обертка для таблицы */}
        <div className="competitors-table-wrapper">
          <CompetitorsTable
            competitors={competitors}
            loading={loading}
            selectedIds={selectedIds}
            onSelectionChange={setSelectedIds}
            onDataChange={handleDataChange}
          />
        </div>

        {/* Массовые действия */}
        <div className="competitors-bulk-actions">
          <button 
            className="btn btn-red" 
            onClick={handleDelete}
            disabled={selectedIds.length === 0}
          >
            Удалить ({selectedIds.length})
          </button>
          <button 
            className="btn btn-blue" 
            onClick={handleCopyDomain}
            disabled={selectedIds.length === 0}
          >
            Копировать домены
          </button>
          <button 
            className="btn btn-green" 
            onClick={() => setShowChangeFieldModal(true)}
            disabled={selectedIds.length === 0}
          >
            Изм. польз. значение
          </button>
          <button 
            className="btn btn-dark-blue" 
            onClick={handleUnselectAll}
            disabled={selectedIds.length === 0}
          >
            Снять выделение
          </button>
        </div>
      </div>

      {/* Модальные окна */}
      <AddCompetitorModal
        show={showAddModal}
        onHide={() => setShowAddModal(false)}
        onAdd={handleAdd}
      />

      <ChangeFieldCompetitorModal
        show={showChangeFieldModal}
        onHide={() => setShowChangeFieldModal(false)}
        onSave={handleChangeField}
        selectedCount={selectedIds.length}
      />

      <ApplyFiltersModal
        show={showFiltersModal}
        onHide={() => setShowFiltersModal(false)}
      />
    </div>
  );
};

export default CompetitorsView;
"""

# Полный исправленный код CompetitorsTable.jsx
COMPETITORS_TABLE_CONTENT = """// frontend/src/components/CompetitorsTable.jsx
import React, { useRef, useEffect, useState } from 'react';
import { HotTable } from '@handsontable/react';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.css';

const CompetitorsTable = ({ 
  competitors, 
  loading, 
  selectedIds, 
  onSelectionChange,
  onDataChange
}) => {
  const hotTableRef = useRef(null);
  const [tableData, setTableData] = useState([]);
  const lastClickedRowRef = useRef(null);

  // Преобразуем данные конкурентов в формат таблицы
  useEffect(() => {
    if (competitors && competitors.length > 0) {
      const data = competitors.map(comp => ({
        selected: selectedIds.includes(comp.id),
        id: comp.id,
        domain: comp.domain,
        org_type: comp.org_type || 'Школа',
        competitiveness: comp.competitiveness || 0,
        notes: comp.notes || ''
      }));
      setTableData(data);
    } else {
      setTableData([]);
    }
  }, [competitors, selectedIds]);

  // Обработка изменения выделения
  const handleAfterSelectionEnd = (row, column, row2, column2) => {
    if (column === 0) return; // Игнорируем клики по чекбоксу
    
    const hot = hotTableRef.current?.hotInstance;
    if (!hot) return;

    const newSelectedIds = [];
    for (let i = Math.min(row, row2); i <= Math.max(row, row2); i++) {
      const rowData = hot.getDataAtRow(i);
      if (rowData && rowData[1]) { // rowData[1] - это ID
        newSelectedIds.push(rowData[1]);
      }
    }
    
    if (newSelectedIds.length > 0) {
      onSelectionChange(newSelectedIds);
    }
  };

  // ✅ ИСПРАВЛЕНО: Обработка клика по чекбоксу
  const handleAfterChange = (changes, source) => {
    if (!changes || source === 'loadData') return;
    
    const hot = hotTableRef.current?.hotInstance;
    if (!hot) return;

    changes.forEach(([row, prop, oldValue, newValue]) => {
      // ✅ Получаем rowData в начале forEach для всех случаев
      const rowData = hot.getDataAtRow(row);
      if (!rowData) return;
      
      const id = rowData[1];
      
      if (prop === 'selected') {
        if (newValue && !selectedIds.includes(id)) {
          onSelectionChange([...selectedIds, id]);
        } else if (!newValue && selectedIds.includes(id)) {
          onSelectionChange(selectedIds.filter(selectedId => selectedId !== id));
        }
      } else if (prop === 'org_type' || prop === 'notes') {
        // Отправляем изменение на сервер
        onDataChange(id, prop, newValue);
      }
    });
  };

  // Обработка Shift+Click
  const handleAfterOnCellMouseDown = (event, coords, td) => {
    if (coords.row < 0) return;
    
    const hot = hotTableRef.current?.hotInstance;
    if (!hot) return;

    if (event.shiftKey && lastClickedRowRef.current !== null) {
      const startRow = Math.min(lastClickedRowRef.current, coords.row);
      const endRow = Math.max(lastClickedRowRef.current, coords.row);
      
      const newSelectedIds = [];
      for (let i = startRow; i <= endRow; i++) {
        const rowData = hot.getDataAtRow(i);
        if (rowData && rowData[1]) {
          newSelectedIds.push(rowData[1]);
        }
      }
      
      onSelectionChange(newSelectedIds);
    }
    
    lastClickedRowRef.current = coords.row;
  };

  // ✅ ИСПРАВЛЕНО: Рендер кнопки "Открыть сайт" - используем обычную функцию
  function openSiteRenderer(instance, td, row, col, prop, value, cellProperties) {
    Handsontable.renderers.TextRenderer.apply(this, arguments);
    
    const rowData = instance.getDataAtRow(row);
    const domain = rowData[2]; // domain находится в 3-й колонке (индекс 2)
    
    if (domain) {
      td.innerHTML = `<a href="https://${domain}" target="_blank" rel="noopener noreferrer" style="color: #4285f4; text-decoration: none;">Открыть сайт</a>`;
    } else {
      td.innerHTML = '';
    }
    
    return td;
  }

  // Конфигурация колонок
  const columns = [
    { 
      data: 'selected', 
      type: 'checkbox', 
      width: 40, 
      className: 'htCenter', 
      title: '', 
      readOnly: false 
    },
    { 
      data: 'id', 
      title: '№', 
      type: 'numeric', 
      width: 50, 
      readOnly: true 
    },
    { 
      data: 'domain', 
      title: 'Домен', 
      type: 'text', 
      width: 300, 
      readOnly: true 
    },
    { 
      data: 'org_type', 
      title: 'Тип организации', 
      type: 'dropdown',
      source: ['Школа', 'База репетиторов', 'Не школа', 'Партнёр'],
      width: 180, 
      readOnly: false 
    },
    { 
      data: 'competitiveness', 
      title: 'Конкурентность', 
      type: 'numeric', 
      width: 130, 
      readOnly: true,
      className: 'htCenter'
    },
    { 
      data: 'notes', 
      title: 'Заметки', 
      type: 'text', 
      width: 250, 
      readOnly: false 
    },
    {
      data: 'domain',
      title: 'Действие',
      width: 120,
      readOnly: true,
      renderer: openSiteRenderer
    }
  ];

  return (
    <div style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
      {loading ? (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          Загрузка данных...
        </div>
      ) : (
        <HotTable
          ref={hotTableRef}
          data={tableData}
          columns={columns}
          colHeaders={true}
          rowHeaders={false}
          width="100%"
          height="100%"
          licenseKey="non-commercial-and-evaluation"
          stretchH="all"
          manualColumnResize={true}
          afterChange={handleAfterChange}
          afterSelectionEnd={handleAfterSelectionEnd}
          afterOnCellMouseDown={handleAfterOnCellMouseDown}
          contextMenu={false}
          selectionMode="range"
          outsideClickDeselects={false}
          fillHandle={false}
          className="keywords-handsontable"
        />
      )}
    </div>
  );
};

export default CompetitorsTable;
"""

# CSS для добавления в main.css
CSS_ADDITIONS = """
/* ===== ДОБАВИТЬ В КОНЕЦ frontend/src/styles/main.css ===== */

/* Обновленные стили для CompetitorsView */
.competitors-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  overflow: hidden;
  gap: 15px;
}

.competitors-table-wrapper {
  flex: 1;
  overflow: hidden;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  background-color: #fff;
  min-height: 300px;
}

.competitors-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.competitors-header {
  flex-shrink: 0;
}

.competitors-actions {
  flex-shrink: 0;
}

.competitors-bulk-actions {
  flex-shrink: 0;
}
"""


def main():
    """Основная функция замены файлов"""
    
    print("=" * 60)
    print("🔧 Скрипт замены CompetitorsView и CompetitorsTable")
    print("=" * 60)
    
    # Определяем пути к файлам
    script_dir = Path(__file__).parent.absolute()
    
    # Проверяем, находимся ли мы в корне проекта
    if not (script_dir / 'frontend').exists():
        print("❌ ОШИБКА: Скрипт должен запускаться из корневой директории проекта!")
        print(f"   Текущая директория: {script_dir}")
        print("   Ожидается структура: ./frontend/src/components/")
        return False
    
    competitors_view_path = script_dir / 'frontend' / 'src' / 'components' / 'CompetitorsView.jsx'
    competitors_table_path = script_dir / 'frontend' / 'src' / 'components' / 'CompetitorsTable.jsx'
    css_path = script_dir / 'frontend' / 'src' / 'styles' / 'main.css'
    
    # Создаем бэкапы
    print("\\n📦 Создание резервных копий...")
    
    if competitors_view_path.exists():
        backup_view = competitors_view_path.with_suffix('.jsx.backup')
        with open(competitors_view_path, 'r', encoding='utf-8') as f:
            with open(backup_view, 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        print(f"   ✅ Бэкап создан: {backup_view}")
    
    if competitors_table_path.exists():
        backup_table = competitors_table_path.with_suffix('.jsx.backup')
        with open(competitors_table_path, 'r', encoding='utf-8') as f:
            with open(backup_table, 'w', encoding='utf-8') as bf:
                bf.write(f.read())
        print(f"   ✅ Бэкап создан: {backup_table}")
    
    # Заменяем файлы
    print("\\n🔄 Замена файлов...")
    
    # CompetitorsView.jsx
    with open(competitors_view_path, 'w', encoding='utf-8') as f:
        f.write(COMPETITORS_VIEW_CONTENT)
    print(f"   ✅ Заменен: {competitors_view_path}")
    
    # CompetitorsTable.jsx
    with open(competitors_table_path, 'w', encoding='utf-8') as f:
        f.write(COMPETITORS_TABLE_CONTENT)
    print(f"   ✅ Заменен: {competitors_table_path}")
    
    # Добавляем CSS
    print("\\n📝 Добавление CSS...")
    if css_path.exists():
        with open(css_path, 'r', encoding='utf-8') as f:
            existing_css = f.read()
        
        # Проверяем, есть ли уже .competitors-content
        if '.competitors-content' not in existing_css:
            with open(css_path, 'a', encoding='utf-8') as f:
                f.write('\\n' + CSS_ADDITIONS)
            print(f"   ✅ CSS добавлен в: {css_path}")
        else:
            print(f"   ℹ️  CSS уже существует в: {css_path}")
    else:
        print(f"   ⚠️  Файл CSS не найден: {css_path}")
    
    print("\\n" + "=" * 60)
    print("✅ ЗАМЕНА УСПЕШНО ЗАВЕРШЕНА!")
    print("=" * 60)
    print("\\n📋 Что было сделано:")
    print("   1. Созданы резервные копии (.jsx.backup)")
    print("   2. Заменен CompetitorsView.jsx (полная версия с кнопками)")
    print("   3. Заменен CompetitorsTable.jsx (исправлена ошибка с arguments)")
    print("   4. Добавлены CSS-стили для правильного layout")
    print("\\n🚀 Следующие шаги:")
    print("   1. Перезапустите React dev server: cd frontend && npm start")
    print("   2. Откройте страницу конкурентов")
    print("   3. Проверьте наличие кнопок над и под таблицей")
    print("\\n⚠️  Если что-то пошло не так:")
    print("   - Восстановите из .backup файлов")
    print("   - Проверьте консоль браузера на ошибки")
    
    return True


if __name__ == '__main__':
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        exit(1)