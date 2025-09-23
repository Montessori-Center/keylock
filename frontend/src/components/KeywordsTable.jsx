// frontend/src/components/KeywordsTable.jsx - С СОХРАНЕНИЕМ ШИРИНЫ СТОЛБЦОВ
import React, { useRef, useEffect, useState } from 'react';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.css';

registerAllModules();

const KeywordsTable = ({ 
  keywords, 
  loading, 
  selectedIds, 
  onSelectionChange, 
  onDataChange,
  visibleColumns = []
}) => {
  const hotTableRef = useRef(null);
  const [tableData, setTableData] = useState([]);
  const [columnWidths, setColumnWidths] = useState({});

  // Все доступные колонки с их настройками
  const allColumns = {
    'selected': { data: 'selected', type: 'checkbox', width: 40, className: 'htCenter', title: '', readOnly: false },
    'id': { data: 'id', title: '№', type: 'numeric', width: 50, readOnly: true },
    'keyword': { data: 'keyword', title: 'Keyword', type: 'text', width: 250, readOnly: false },
    'criterion_type': { data: 'criterion_type', title: 'Criterion Type', type: 'dropdown', 
      source: ['Phrase', 'Broad', 'Exact'], width: 120, readOnly: false },
    'max_cpc': { data: 'max_cpc', title: 'Max CPC', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 80, readOnly: false },
    'max_cpm': { data: 'max_cpm', title: 'Max CPM', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 80, readOnly: false },
    'max_cpv': { data: 'max_cpv', title: 'Max CPV', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 80, readOnly: false },
    'first_page_bid': { data: 'first_page_bid', title: 'First page bid', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 120, readOnly: true },
    'top_of_page_bid': { data: 'top_of_page_bid', title: 'Top of page bid', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 120, readOnly: true },
    'first_position_bid': { data: 'first_position_bid', title: 'First position bid', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 120, readOnly: true },
    'quality_score': { data: 'quality_score', title: 'Quality score', type: 'numeric', width: 100, readOnly: true },
    'landing_page_experience': { data: 'landing_page_experience', title: 'Landing page experience', type: 'text', width: 150, readOnly: true },
    'expected_ctr': { data: 'expected_ctr', title: 'Expected CTR', type: 'text', width: 100, readOnly: true },
    'ad_relevance': { data: 'ad_relevance', title: 'Ad relevance', type: 'text', width: 100, readOnly: true },
    'final_url': { data: 'final_url', title: 'Final URL', type: 'text', width: 200, readOnly: false },
    'final_mobile_url': { data: 'final_mobile_url', title: 'Final mobile URL', type: 'text', width: 200, readOnly: false },
    'tracking_template': { data: 'tracking_template', title: 'Tracking template', type: 'text', width: 200, readOnly: false },
    'final_url_suffix': { data: 'final_url_suffix', title: 'Final URL suffix', type: 'text', width: 150, readOnly: false },
    'custom_parameters': { data: 'custom_parameters', title: 'Custom parameters', type: 'text', width: 150, readOnly: false },
    'status': { data: 'status', title: 'Status', type: 'dropdown', source: ['Enabled', 'Paused'], width: 100, readOnly: false },
    'approval_status': { data: 'approval_status', title: 'Approval Status', type: 'text', width: 120, readOnly: true },
    'comment': { data: 'comment', title: 'Comment', type: 'text', width: 150, readOnly: false },
    'has_ads': { data: 'has_ads', title: 'Есть реклама?', type: 'dropdown', source: ['Да', 'Нет'], width: 120, className: 'htCenter', readOnly: false },
    'has_school_sites': { data: 'has_school_sites', title: 'Есть сайты школ?', type: 'dropdown', source: ['Да', 'Нет'], width: 140, className: 'htCenter', readOnly: false },
    'has_google_maps': { data: 'has_google_maps', title: 'Есть Google карты?', type: 'dropdown', source: ['Да', 'Нет'], width: 150, className: 'htCenter', readOnly: false },
    'has_our_site': { data: 'has_our_site', title: 'Есть наш сайт?', type: 'dropdown', source: ['Да', 'Нет'], width: 130, className: 'htCenter', readOnly: false },
    'intent_type': { data: 'intent_type', title: 'Тип интента', type: 'dropdown', source: ['Коммерческий', 'Информационный', 'Навигационный', 'Транзакционный'], width: 130, readOnly: false },
    'recommendation': { data: 'recommendation', title: 'Рекомендация', type: 'text', width: 150, readOnly: false },
    'avg_monthly_searches': { data: 'avg_monthly_searches', title: 'Среднее число запросов в месяц', type: 'numeric', width: 180, readOnly: true },
    'three_month_change': { data: 'three_month_change', title: 'Изменение за три месяца', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 160, readOnly: true },
    'yearly_change': { data: 'yearly_change', title: 'Изменение за год', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 130, readOnly: true },
    'competition': { data: 'competition', title: 'Конкуренция', type: 'text', width: 110, readOnly: true },
    'competition_percent': { data: 'competition_percent', title: 'Конкуренция, %', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 120, readOnly: true },
    'min_top_of_page_bid': { data: 'min_top_of_page_bid', title: 'Ставка для показа вверху стр. (мин.)', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 200, readOnly: true },
    'max_top_of_page_bid': { data: 'max_top_of_page_bid', title: 'Ставка для показа вверху стр. (макс.)', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 200, readOnly: true },
    'ad_impression_share': { data: 'ad_impression_share', title: 'Ad impression share', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 150, readOnly: true },
    'organic_average_position': { data: 'organic_average_position', title: 'Organic average position', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 180, readOnly: true },
    'organic_impression_share': { data: 'organic_impression_share', title: 'Organic impression share', type: 'numeric', numericFormat: { pattern: '0.00' }, width: 180, readOnly: true },
    'labels': { data: 'labels', title: 'Labels', type: 'text', width: 150, readOnly: false }
  };

  // Загрузка сохраненных ширин столбцов при монтировании
  useEffect(() => {
    const savedWidths = localStorage.getItem('keywordsTableColumnWidths');
    if (savedWidths) {
      try {
        const widths = JSON.parse(savedWidths);
        setColumnWidths(widths);
        console.log('📏 Loaded saved column widths:', widths);
      } catch (e) {
        console.error('Error loading column widths:', e);
      }
    }
  }, []);

  // Формируем колонки на основе настроек видимости и сохраненных ширин
  const getVisibleColumns = () => {
      // Порядок колонок должен соответствовать порядку в настройках
      const columnOrder = [
        'selected',  // Чекбокс всегда первый
        'id',
        'keyword',
        'criterion_type',
        'max_cpc',
        'max_cpm',
        'max_cpv',
        'first_page_bid',
        'top_of_page_bid',
        'first_position_bid',
        'quality_score',
        'landing_page_experience',
        'expected_ctr',
        'ad_relevance',
        'final_url',
        'final_mobile_url',
        'tracking_template',
        'final_url_suffix',
        'custom_parameters',
        'status',
        'approval_status',
        'comment',
        'has_ads',
        'has_school_sites',
        'has_google_maps',
        'has_our_site',
        'intent_type',
        'recommendation',
        'avg_monthly_searches',
        'three_month_change',
        'yearly_change',
        'competition',
        'competition_percent',
        'min_top_of_page_bid',
        'max_top_of_page_bid',
        'ad_impression_share',
        'organic_average_position',
        'organic_impression_share',
        'labels'
      ];
    
      // Дефолтные колонки если настройки не заданы
      const defaultColumns = [
        'selected', 'id', 'keyword', 'criterion_type', 'max_cpc', 'status', 'comment',
        'has_ads', 'has_school_sites', 'has_google_maps', 'has_our_site',
        'intent_type', 'recommendation', 'avg_monthly_searches',
        'three_month_change', 'yearly_change', 'competition',
        'competition_percent', 'min_top_of_page_bid', 'max_top_of_page_bid'
      ];
      
      // Определяем какие колонки показывать
      let columnsToShow;
      
      if (visibleColumns && visibleColumns.length > 0) {
        // Если есть настройки видимости, используем их
        // Но сохраняем порядок из columnOrder
        columnsToShow = columnOrder.filter(key => {
          // 'selected' всегда показываем
          if (key === 'selected') return true;
          // Остальные колонки показываем если они в visibleColumns
          return visibleColumns.includes(key);
        });
      } else {
        // Если настроек нет, используем дефолтные колонки
        columnsToShow = defaultColumns;
      }
      
      // Преобразуем в объекты колонок с применением сохраненных ширин
      return columnsToShow
        .filter(key => allColumns[key]) // Проверяем что колонка существует
        .map(key => {
          const column = { ...allColumns[key] };
          // Применяем сохраненную ширину если есть
          if (columnWidths[key]) {
            column.width = columnWidths[key];
          }
          return column;
        });
    };

  // Обработчик изменения ширины столбца
  const handleAfterColumnResize = (newSize, column, isDoubleClick) => {
    const instance = hotTableRef.current?.hotInstance;
    if (!instance) return;

    // Получаем текущие колонки
    const columns = getVisibleColumns();
    const columnKey = columns[column]?.data;
    
    if (columnKey) {
      // Обновляем сохраненные ширины
      const newWidths = {
        ...columnWidths,
        [columnKey]: newSize
      };
      
      setColumnWidths(newWidths);
      
      // Сохраняем в localStorage
      localStorage.setItem('keywordsTableColumnWidths', JSON.stringify(newWidths));
      console.log(`📏 Saved column width: ${columnKey} = ${newSize}px`);
    }
  };

  // Преобразование данных для таблицы
  useEffect(() => {
    const data = keywords.map(keyword => ({
      selected: selectedIds.includes(keyword.id),
      id: keyword.id,
      keyword: keyword.keyword,
      criterion_type: keyword.criterion_type,
      max_cpc: keyword.max_cpc,
      max_cpm: keyword.max_cpm,
      max_cpv: keyword.max_cpv,
      first_page_bid: keyword.first_page_bid,
      top_of_page_bid: keyword.top_of_page_bid,
      first_position_bid: keyword.first_position_bid,
      quality_score: keyword.quality_score,
      landing_page_experience: keyword.landing_page_experience,
      expected_ctr: keyword.expected_ctr,
      ad_relevance: keyword.ad_relevance,
      final_url: keyword.final_url,
      final_mobile_url: keyword.final_mobile_url,
      tracking_template: keyword.tracking_template,
      final_url_suffix: keyword.final_url_suffix,
      custom_parameters: keyword.custom_parameters,
      status: keyword.status,
      approval_status: keyword.approval_status,
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
      max_top_of_page_bid: keyword.max_top_of_page_bid,
      ad_impression_share: keyword.ad_impression_share,
      organic_average_position: keyword.organic_average_position,
      organic_impression_share: keyword.organic_impression_share,
      labels: keyword.labels,
      is_new: keyword.is_new || false,
      batch_color: keyword.batch_color
    }));
    setTableData(data);
  }, [keywords, selectedIds]);

  // Применение стилей для новых записей
  useEffect(() => {
    if (!hotTableRef.current?.hotInstance || tableData.length === 0) return;
    
    const instance = hotTableRef.current.hotInstance;
    
    instance.updateSettings({
      cells: function(row, col) {
        const cellProperties = {};
        const rowData = this.instance.getSourceDataAtRow(row);
        
        if (rowData && rowData.is_new && rowData.batch_color) {
          cellProperties.renderer = function(hotInstance, td, row, col, prop, value, cellProperties) {
            Handsontable.renderers.getRenderer(cellProperties.type)(hotInstance, td, row, col, prop, value, cellProperties);
            
            td.style.backgroundColor = rowData.batch_color;
            td.style.fontWeight = 'bold';
            
            if (col === 0) {
              td.style.borderLeft = `4px solid ${rowData.batch_color}`;
            }
            
            return td;
          };
        }
        
        return cellProperties;
      }
    });
    
    instance.render();
    
  }, [tableData]);

  // Обновление таблицы при изменении visibleColumns
  useEffect(() => {
    if (!hotTableRef.current?.hotInstance) return;
    
    const instance = hotTableRef.current.hotInstance;
    const newColumns = getVisibleColumns();
    
    // Обновляем настройки колонок
    instance.updateSettings({
      columns: newColumns,
      colHeaders: newColumns.map(col => col.title || '')
    });
    
    console.log('📊 Updated visible columns:', newColumns.map(c => c.data));
  }, [visibleColumns, columnWidths]); // Добавили columnWidths в зависимости

  // Обработка изменений в таблице
  const handleAfterChange = (changes, source) => {
    if (source === 'loadData' || !changes) return;
    
    const checkboxChanges = changes.filter(([row, prop]) => prop === 'selected');
    if (checkboxChanges.length > 0) {
      const newSelectedIds = [];
      tableData.forEach((row, index) => {
        const change = checkboxChanges.find(([r]) => r === index);
        if (change) {
          if (change[3]) {
            newSelectedIds.push(row.id);
          }
        } else if (row.selected) {
          newSelectedIds.push(row.id);
        }
      });
      onSelectionChange(newSelectedIds);
    }
    
    const dataChanges = changes.filter(([row, prop]) => prop !== 'selected');
    if (dataChanges.length > 0 && onDataChange) {
      onDataChange(dataChanges);
    }
  };

  if (loading) {
    return <div className="loading">Загрузка данных...</div>;
  }

  const visibleColumnsConfig = getVisibleColumns();

  return (
    <div className="keywords-table-container">
      <HotTable
        ref={hotTableRef}
        data={tableData}
        columns={visibleColumnsConfig}
        colHeaders={true}
        rowHeaders={false}
        height="calc(100vh - 300px)"
        width="100%"
        stretchH="all"
        autoWrapRow={true}
        autoWrapCol={true}
        licenseKey="non-commercial-and-evaluation"
        afterChange={handleAfterChange}
        afterColumnResize={handleAfterColumnResize}
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