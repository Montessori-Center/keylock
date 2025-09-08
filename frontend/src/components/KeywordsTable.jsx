// frontend/src/components/KeywordsTable.jsx
import React, { useRef, useEffect, useState } from 'react';
import { HotTable } from '@handsontable/react';
import Handsontable from 'handsontable';
import { registerAllModules } from 'handsontable/registry';
import 'handsontable/dist/handsontable.full.css';

// Регистрируем все модули Handsontable
registerAllModules();

const KeywordsTable = ({ keywords, loading, selectedIds, onSelectionChange, onDataChange }) => {
  const hotTableRef = useRef(null);
  const [tableData, setTableData] = useState([]);

  // Колонки для отображения
  const columns = [
    { data: 'selected', type: 'checkbox', width: 40, className: 'htCenter' },
    { data: 'id', title: '№', type: 'numeric', width: 50, readOnly: true },
    { data: 'keyword', title: 'Keyword', type: 'text', width: 250 },
    { data: 'criterion_type', title: 'Criterion Type', type: 'dropdown', 
      source: ['Phrase', 'Broad', 'Exact'], width: 120 },
    { data: 'max_cpc', title: 'Max CPC', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 80 },
    { data: 'status', title: 'Status', type: 'dropdown',
      source: ['Enabled', 'Paused'], width: 100 },
    { data: 'comment', title: 'Comment', type: 'text', width: 150 },
    { data: 'has_ads', title: 'Есть реклама?', type: 'dropdown',
      source: ['Да', 'Нет'], width: 120, className: 'htCenter' },
    { data: 'has_school_sites', title: 'Есть сайты школ?', type: 'dropdown',
      source: ['Да', 'Нет'], width: 140, className: 'htCenter' },
    { data: 'has_google_maps', title: 'Есть Google карты?', type: 'dropdown',
      source: ['Да', 'Нет'], width: 150, className: 'htCenter' },
    { data: 'has_our_site', title: 'Есть наш сайт?', type: 'dropdown',
      source: ['Да', 'Нет'], width: 130, className: 'htCenter' },
    { data: 'intent_type', title: 'Тип интента', type: 'dropdown',
      source: ['Коммерческий', 'Информационный', 'Навигационный', 'Транзакционный'], width: 130 },
    { data: 'recommendation', title: 'Рекомендация', type: 'text', width: 150 },
    { data: 'avg_monthly_searches', title: 'Среднее число запросов в месяц', type: 'numeric', width: 180 },
    { data: 'three_month_change', title: 'Изменение за три месяца', type: 'numeric', 
      numericFormat: { pattern: '0.00' }, width: 160 },
    { data: 'yearly_change', title: 'Изменение за год', type: 'numeric',
      numericFormat: { pattern: '0.00' }, width: 130 },
    { data: 'competition', title: 'Конкуренция', type: 'text', width: 110 },
    { data: 'competition_percent', title: 'Конкуренция, %', type: 'numeric',
      numericFormat: { pattern: '0.00' }, width: 120 },
    { data: 'min_top_of_page_bid', title: 'Ставка для показа вверху стр. (мин.)', type: 'numeric',
      numericFormat: { pattern: '0.00' }, width: 200 },
    { data: 'max_top_of_page_bid', title: 'Ставка для показа вверху стр. (макс.)', type: 'numeric',
      numericFormat: { pattern: '0.00' }, width: 200 }
  ];

  // Преобразование данных для таблицы
  useEffect(() => {
    const data = keywords.map(keyword => ({
      selected: selectedIds.includes(keyword.id),
      id: keyword.id,
      keyword: keyword.keyword,
      criterion_type: keyword.criterion_type,
      max_cpc: keyword.max_cpc,
      status: keyword.status,
      comment: keyword.comment,
      has_ads: keyword.has_ads ? 'Да' : 'Нет',
      has_school_sites: keyword.has_school_sites ? 'Да' : 'Нет',
      has_google_maps: keyword.has_google_maps ? 'Да' : 'Нет',
      has_our_site: keyword.has_our_site ? 'Да' : 'Нет',
      intent_type: keyword.intent_type || 'Информационный',
      recommendation: keyword.recommendation,
      avg_monthly_searches: keyword.avg_monthly_searches,
      three_month_change: keyword.three_month_change,
      yearly_change: keyword.yearly_change,
      competition: keyword.competition,
      competition_percent: keyword.competition_percent,
      min_top_of_page_bid: keyword.min_top_of_page_bid,
      max_top_of_page_bid: keyword.max_top_of_page_bid
    }));
    setTableData(data);
    
    // Обновляем таблицу принудительно если изменились selectedIds
    if (hotTableRef.current && hotTableRef.current.hotInstance) {
      hotTableRef.current.hotInstance.loadData(data);
    }
  }, [keywords, selectedIds]);

  // Обработка изменений в таблице
  const handleAfterChange = (changes, source) => {
    if (source === 'loadData' || !changes) return;
    
    // Обработка изменения чекбоксов
    const checkboxChanges = changes.filter(([row, prop]) => prop === 'selected');
    if (checkboxChanges.length > 0) {
      const newSelectedIds = [];
      tableData.forEach((row, index) => {
        const change = checkboxChanges.find(([r]) => r === index);
        if (change) {
          if (change[3]) { // new value is true
            newSelectedIds.push(row.id);
          }
        } else if (row.selected) {
          newSelectedIds.push(row.id);
        }
      });
      onSelectionChange(newSelectedIds);
    }
    
    // Передаем изменения наверх для сохранения
    const dataChanges = changes.filter(([row, prop]) => prop !== 'selected');
    if (dataChanges.length > 0 && onDataChange) {
      onDataChange(dataChanges);
    }
  };

  // Настройка цветов для ячеек
  const getCellRenderer = () => {
    return function(instance, td, row, col, prop, value, cellProperties) {
      const defaultRenderer = Handsontable.renderers.getRenderer(cellProperties.type || 'text');
      defaultRenderer.apply(this, arguments);
      
      // Цветовая схема для полей
      if (prop === 'has_ads' || prop === 'has_school_sites' || prop === 'has_google_maps' || prop === 'has_our_site') {
        if (value === 'Да') {
          td.style.backgroundColor = '#d4edda';
          td.style.color = '#155724';
        } else if (value === 'Нет') {
          td.style.backgroundColor = '#f8d7da';
          td.style.color = '#721c24';
        }
      }
      
      if (prop === 'intent_type') {
        if (value === 'Коммерческий') {
          td.style.backgroundColor = '#d4edda';
        } else if (value === 'Информационный') {
          td.style.backgroundColor = '#d1ecf1';
        }
      }
      
      if (prop === 'status') {
        if (value === 'Enabled') {
          td.style.backgroundColor = '#d4edda';
        } else if (value === 'Paused') {
          td.style.backgroundColor = '#fff3cd';
        }
      }
      
      // Выделение строки если она выбрана
      if (tableData[row]?.selected) {
        td.style.backgroundColor = '#e3f2fd';
      }
    };
  };

  if (loading) {
    return <div className="loading">Загрузка данных...</div>;
  }

  return (
    <div className="keywords-table-container">
      <HotTable
        ref={hotTableRef}
        data={tableData}
        columns={columns}
        colHeaders={true}
        rowHeaders={false}
        height="calc(100vh - 300px)"
        width="100%"
        stretchH="all"
        autoWrapRow={true}
        autoWrapCol={true}
        licenseKey="non-commercial-and-evaluation"
        afterChange={handleAfterChange}
        cells={getCellRenderer}
        manualColumnResize={true}
        manualRowResize={true}
        contextMenu={true}
        filters={true}
        dropdownMenu={true}
        columnSorting={true}
        className="keywords-handsontable"
      />
    </div>
  );
};

export default KeywordsTable;