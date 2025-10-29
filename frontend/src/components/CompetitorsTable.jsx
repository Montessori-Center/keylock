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

  // ✅ ИСПРАВЛЕНО: Обработка изменений с учётом сортировки
    const handleAfterChange = useCallback((changes, source) => {
      if (source === 'loadData' || !changes) return;
      
      const checkboxChanges = changes.filter(([row, prop]) => prop === 'selected');
      if (checkboxChanges.length > 0) {
        const instance = hotTableRef.current?.hotInstance;
        if (!instance) return;
    
        const newSelectedIds = [...selectedIds];
        
        checkboxChanges.forEach(([visualRow, prop, oldValue, newValue]) => {
          // ✅ Преобразуем визуальный индекс в физический
          const physicalRow = instance.toPhysicalRow(visualRow);
          const rowData = tableData[physicalRow];
          
          if (rowData) {
            const rowId = rowData.id;
            
            if (newValue && !newSelectedIds.includes(rowId)) {
              newSelectedIds.push(rowId);
            } else if (!newValue && newSelectedIds.includes(rowId)) {
              const index = newSelectedIds.indexOf(rowId);
              newSelectedIds.splice(index, 1);
            }
          }
        });
        
        onSelectionChange(newSelectedIds);
      }
      
      // ✅ ИСПРАВЛЕНО: Обработка изменений данных (не чекбоксов)
      const dataChanges = changes.filter(([row, prop]) => prop !== 'selected');
      if (dataChanges.length > 0 && onDataChange) {
        const instance = hotTableRef.current?.hotInstance;
        if (!instance) return;
    
        // Обрабатываем каждое изменение
        dataChanges.forEach(([visualRow, prop, oldValue, newValue]) => {
          // ✅ Преобразуем визуальный индекс в физический
          const physicalRow = instance.toPhysicalRow(visualRow);
          const rowData = tableData[physicalRow];
          
          if (rowData && rowData.id) {
            // ✅ Вызываем onDataChange с правильными параметрами: (id, field, value)
            onDataChange(rowData.id, prop, newValue);
          }
        });
      }
    }, [tableData, selectedIds, onSelectionChange, onDataChange]);

  const handleAfterSelectionEnd = (row, column, row2, column2) => {
    if (column === 0) return;
    
    const hot = hotTableRef.current?.hotInstance;
    if (!hot) return;

    const newSelectedIds = [];
    for (let i = Math.min(row, row2); i <= Math.max(row, row2); i++) {
      const rowData = hot.getDataAtRow(i);
      if (rowData && rowData[1]) {
        newSelectedIds.push(rowData[1]);
      }
    }

    if (newSelectedIds.length > 0) {
      const updatedData = tableData.map(item => ({
        ...item,
        selected: newSelectedIds.includes(item.id)
      }));
      
      hot.loadData(updatedData);
      onSelectionChange(newSelectedIds);
    }
  };

  // ✅ ИСПРАВЛЕНО: Перехватываем клики по чекбоксам с преобразованием индексов
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
    
        const visualRow = coords.row;  // ✅ Визуальный индекс
        const physicalRow = instance.toPhysicalRow(visualRow);  // ✅ Физический индекс
    
        // ✅ SHIFT-ВЫДЕЛЕНИЕ
        if (e.shiftKey && lastClickedRowRef.current !== null) {
          e.preventDefault();
          e.stopPropagation();
    
          const visualStartRow = lastClickedRowRef.current;
          const physicalStartRow = instance.toPhysicalRow(visualStartRow);
          
          const startRow = Math.min(physicalStartRow, physicalRow);
          const endRow = Math.max(physicalStartRow, physicalRow);
    
          console.log(`✅ Shift-click competitors: visual [${Math.min(visualStartRow, visualRow)}-${Math.max(visualStartRow, visualRow)}] -> physical [${startRow}-${endRow}]`);
    
          const shouldSelect = !checkbox.checked;
    
          const rangeIds = [];
          for (let i = startRow; i <= endRow; i++) {
            if (tableData[i]) {
              rangeIds.push(tableData[i].id);
            }
          }
    
          let newSelectedIds;
          if (shouldSelect) {
            newSelectedIds = [...new Set([...selectedIds, ...rangeIds])];
          } else {
            newSelectedIds = selectedIds.filter(id => !rangeIds.includes(id));
          }
    
          onSelectionChange(newSelectedIds);
    
          const newData = tableData.map(row => ({
            ...row,
            selected: newSelectedIds.includes(row.id)
          }));
          
          instance.loadData(newData);
          
          return;
        }
    
        // ✅ ОБЫЧНЫЙ КЛИК
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
          afterSelectionEnd={handleAfterSelectionEnd}
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