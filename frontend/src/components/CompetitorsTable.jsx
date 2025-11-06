// frontend/src/components/CompetitorsTable.jsx - ИСПРАВЛЕНО БЕЗ ПРЕДУПРЕЖДЕНИЙ
import React, { useRef, useEffect, useState, useCallback } from 'react';
import { HotTable } from '@handsontable/react';
import { registerAllModules } from 'handsontable/registry';
import Handsontable from 'handsontable';
import 'handsontable/dist/handsontable.full.css';

registerAllModules();

const CompetitorsTable = ({ 
  competitors, 
  loading, 
  selectedIds, 
  onSelectionChange,
  onDataChange
}) => {
  const hotTableRef = useRef(null);
  const [tableData, setTableData] = useState([]);
  const [columnWidths, setColumnWidths] = useState({});
  const lastClickedRowRef = useRef(null);

  // ✅ Загрузка сохраненных ширин столбцов при монтировании
  useEffect(() => {
    const savedWidths = localStorage.getItem('competitorsTableColumnWidths');
    if (savedWidths) {
      try {
        const widths = JSON.parse(savedWidths);
        setColumnWidths(widths);
        console.log('📏 Loaded saved competitors column widths:', widths);
      } catch (e) {
        console.error('Error loading column widths:', e);
      }
    }
  }, []);

  // ✅ Рендерер для ссылки "Открыть сайт" - определяем до getColumns
  function openSiteRenderer(instance, td, row, col, prop, value, cellProperties) {
    Handsontable.renderers.TextRenderer(instance, td, row, col, prop, value, cellProperties);
    
    const rowData = instance.getDataAtRow(row);
    const domain = rowData[2];
    
    if (domain) {
      td.innerHTML = '';
      const link = document.createElement('a');
      link.href = `https://${domain}`;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.textContent = 'Открыть сайт';
      link.style.color = '#4285f4';
      link.style.textDecoration = 'none';
      link.style.cursor = 'pointer';
      
      link.addEventListener('mousedown', (e) => {
        e.stopPropagation();
      });
      link.addEventListener('click', (e) => {
        e.stopPropagation();
      });
      
      td.appendChild(link);
    } else {
      td.innerHTML = '';
    }
    
    return td;
  }

  // ✅ Функция для получения колонок с применёнными ширинами - обёрнута в useCallback
  const getColumns = useCallback(() => {
    return [
      { 
        data: 'selected', 
        type: 'checkbox', 
        width: columnWidths['selected'] || 40, 
        className: 'htCenter', 
        title: '', 
        readOnly: false 
      },
      { 
        data: 'id', 
        title: '№', 
        type: 'numeric', 
        width: columnWidths['id'] || 50, 
        readOnly: true 
      },
      { 
        data: 'domain', 
        title: 'Домен', 
        type: 'text', 
        width: columnWidths['domain'] || 300, 
        readOnly: true 
      },
      { 
        data: 'org_type', 
        title: 'Тип организации', 
        type: 'dropdown',
        source: ['Школа', 'База репетиторов', 'Не школа', 'Партнёр'],
        width: columnWidths['org_type'] || 180, 
        readOnly: false 
      },
      { 
        data: 'competitiveness', 
        title: 'Конкурентность', 
        type: 'numeric', 
        width: columnWidths['competitiveness'] || 130, 
        readOnly: true,
        className: 'htCenter'
      },
      { 
        data: 'notes', 
        title: 'Заметки', 
        type: 'text', 
        width: columnWidths['notes'] || 250, 
        readOnly: false 
      },
      {
        data: 'domain',
        title: 'Действие',
        width: columnWidths['action'] || 120,
        readOnly: true,
        renderer: openSiteRenderer
      }
    ];
  }, [columnWidths]); // ✅ Зависит только от columnWidths

  // ✅ Обработчик изменения ширины столбца
  const handleAfterColumnResize = useCallback((newSize, column) => {
    const columns = getColumns();
    const columnKey = columns[column]?.data;
    
    if (columnKey) {
      const newWidths = {
        ...columnWidths,
        [columnKey]: newSize
      };
      
      setColumnWidths(newWidths);
      localStorage.setItem('competitorsTableColumnWidths', JSON.stringify(newWidths));
      console.log(`📏 Saved competitors column width: ${columnKey} = ${newSize}px`);
    }
  }, [columnWidths, getColumns]);

  // Преобразуем данные конкурентов в формат таблицы
    useEffect(() => {
      if (competitors && competitors.length > 0) {
        const data = competitors.map(comp => ({
          selected: selectedIds.includes(comp.id),
          id: comp.id,
          domain: comp.domain,
          org_type: comp.org_type || 'Школа',
          competitiveness: comp.competitiveness || 0,
          notes: comp.notes || '',
          is_new: comp.is_new || false
        }));
        
        // ✅ Обновляем данные БЕЗ пересоздания таблицы (сохраняет сортировку)
        if (hotTableRef.current?.hotInstance && tableData.length > 0) {
          const instance = hotTableRef.current.hotInstance;
          
          // Обновляем только изменившиеся строки
          instance.batch(() => {
            data.forEach((newRow, idx) => {
              const oldRow = tableData[idx];
              if (oldRow && JSON.stringify(oldRow) !== JSON.stringify(newRow)) {
                // Обновляем через физический индекс
                Object.keys(newRow).forEach(key => {
                  instance.setDataAtRowProp(idx, key, newRow[key]);
                });
              }
            });
          });
        }
        
        setTableData(data);
      } else {
        setTableData([]);
      }
    }, [competitors, selectedIds]);

  // ✅ Применение стилей для новых записей
  useEffect(() => {
    if (!hotTableRef.current?.hotInstance || tableData.length === 0) return;
    
    const instance = hotTableRef.current.hotInstance;
    
    instance.updateSettings({
      cells: function(row) {
        const cellProperties = {};
        const rowData = this.instance.getSourceDataAtRow(row);
        
        if (rowData && rowData.is_new) {
          cellProperties.className = 'new-competitor-row';
        }
        
        return cellProperties;
      }
    });
    
    instance.render();
  }, [tableData]);

  // ✅ Обновление таблицы при изменении columnWidths - теперь без предупреждений
  useEffect(() => {
    if (!hotTableRef.current?.hotInstance) return;
    
    const instance = hotTableRef.current.hotInstance;
    const newColumns = getColumns();
    
    instance.updateSettings({
      columns: newColumns,
      colHeaders: newColumns.map(col => col.title || '')
    });
    
    console.log('📊 Updated competitors columns with widths');
  }, [getColumns]);


  const handleAfterChange = (changes, source) => {
    if (source === 'loadData' || !changes) return;
    
    const checkboxChanges = changes.filter(([row, prop]) => prop === 'selected');
    if (checkboxChanges.length > 0) {
      const instance = hotTableRef.current?.hotInstance;
      if (!instance) return;

      // ✅ ОПТИМИЗАЦИЯ: Создаём Map ОДИН РАЗ
      const rowIdMap = new Map(tableData.map((row, idx) => [idx, row.id]));
      const newSelectedIds = new Set(selectedIds);
      
      checkboxChanges.forEach(([visualRow, prop, oldValue, newValue]) => {
        const physicalRow = instance.toPhysicalRow(visualRow);
        const rowId = rowIdMap.get(physicalRow);
        
        if (rowId) {
          if (newValue) {
            newSelectedIds.add(rowId);
          } else {
            newSelectedIds.delete(rowId);
          }
        }
      });
      
      // ✅ Обновляем состояние только если изменилось
      const newArray = Array.from(newSelectedIds);
      if (newArray.length !== selectedIds.length || 
          !selectedIds.every(id => newSelectedIds.has(id))) {
        onSelectionChange(newArray);
      }
      return; // Не обрабатываем dataChanges для чекбоксов
    }
    
    const dataChanges = changes.filter(([row, prop]) => prop !== 'selected');
    if (dataChanges.length > 0 && onDataChange) {
      onDataChange(dataChanges);
    }
  };

  useEffect(() => {
    if (!hotTableRef.current?.hotInstance) return;
  
    const handleMouseDown = (e) => {
      const checkbox = e.target.closest('input[type="checkbox"]');
      if (!checkbox) return;
  
      const td = checkbox.closest('td');
      if (!td) return;
  
      const instance = hotTableRef.current.hotInstance;
      const coords = instance.getCoords(td);
      
      if (!coords || coords.col !== 0) return;
  
      const visualRow = coords.row;
  
      // ✅ SHIFT-ВЫДЕЛЕНИЕ - работаем с ВИЗУАЛЬНЫМИ индексами
      if (e.shiftKey && lastClickedRowRef.current !== null) {
        e.preventDefault();
        e.stopPropagation();

        const visualStartRow = lastClickedRowRef.current; // Визуальный индекс!
        
        // Определяем визуальный диапазон
        const visualStart = Math.min(visualStartRow, visualRow);
        const visualEnd = Math.max(visualStartRow, visualRow);
  
        const shouldSelect = !checkbox.checked;
  
        // ✅ Собираем ID строк в ВИЗУАЛЬНОМ диапазоне
        const rangeIds = [];
        for (let visualIdx = visualStart; visualIdx <= visualEnd; visualIdx++) {
          const physicalIdx = instance.toPhysicalRow(visualIdx);
          if (tableData[physicalIdx]) {
            rangeIds.push(tableData[physicalIdx].id);
          }
        }
  
        // ✅ ОПТИМИЗАЦИЯ: Используем Set для быстрых операций
        const newSelectedSet = new Set(selectedIds);
        
        if (shouldSelect) {
          rangeIds.forEach(id => newSelectedSet.add(id));
        } else {
          rangeIds.forEach(id => newSelectedSet.delete(id));
        }
  
        const newSelectedIds = Array.from(newSelectedSet);
        onSelectionChange(newSelectedIds);
        
        // Чекбоксы обновятся автоматически через пересоздание tableData
        return;
      }
  
      // ✅ ОБЫЧНЫЙ КЛИК - сохраняем ВИЗУАЛЬНЫЙ индекс
      lastClickedRowRef.current = visualRow;
    };
  
    const tableElement = hotTableRef.current.hotInstance.rootElement;
    tableElement.addEventListener('mousedown', handleMouseDown, true);
  
    return () => {
      tableElement.removeEventListener('mousedown', handleMouseDown, true);
    };
  }, [tableData, selectedIds, onSelectionChange]);

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
          columns={getColumns()}
          colHeaders={true}
          rowHeaders={false}
          width="100%"
          height="100%"
          licenseKey="non-commercial-and-evaluation"
          stretchH="all"
          manualColumnResize={true}
          afterChange={handleAfterChange}
          afterColumnResize={handleAfterColumnResize}
          contextMenu={true}
          selectionMode="range"
          outsideClickDeselects={false}
          fillHandle={false}
          filters={true}
          dropdownMenu={true}
          columnSorting={true}
          className="keywords-handsontable"
        />
      )}
    </div>
  );
};

export default CompetitorsTable;