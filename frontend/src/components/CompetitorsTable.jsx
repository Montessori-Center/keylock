// frontend/src/components/CompetitorsTable.jsx - ПОЛНАЯ ВЕРСИЯ
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

  // ✅ Обработчик изменения ширины столбца
  const handleAfterColumnResize = (newSize, column) => {
    const instance = hotTableRef.current?.hotInstance;
    if (!instance) return;

    const columns = ['selected', 'id', 'domain', 'org_type', 'competitiveness', 'notes', 'action'];
    const columnKey = columns[column];
    
    if (columnKey) {
      const newWidths = {
        ...columnWidths,
        [columnKey]: newSize
      };
      
      setColumnWidths(newWidths);
      localStorage.setItem('competitorsTableColumnWidths', JSON.stringify(newWidths));
      console.log(`📏 Saved competitors column width: ${columnKey} = ${newSize}px`);
    }
  };

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

  const handleAfterChange = (changes, source) => {
    if (!changes || source === 'loadData') return;

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
      dataChanges.forEach(([row, prop, oldValue, newValue]) => {
        const rowData = tableData[row];
        if (rowData && prop && newValue !== oldValue) {
          onDataChange(rowData.id, prop, newValue);
        }
      });
    }
  };

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

  // ✅ ИСПРАВЛЕНО: SHIFT-выделение (скопировано из KeywordsTable)
  useEffect(() => {
    const instance = hotTableRef.current?.hotInstance;
    if (!instance) return;

    const handleMouseDown = (e) => {
      // Проверяем, что клик по чекбоксу
      const checkbox = e.target.closest('input[type="checkbox"]');
      if (!checkbox) return;

      // Проверяем, что это чекбокс из нашей таблицы
      const td = checkbox.closest('td');
      if (!td) return;

      const coords = instance.getCoords(td);
      
      if (!coords || coords.col !== 0) return; // Только первая колонка (чекбоксы)

      const currentRow = coords.row;

      // ✅ SHIFT-ВЫДЕЛЕНИЕ
      if (e.shiftKey && lastClickedRowRef.current !== null) {
        e.preventDefault();
        e.stopPropagation();

        const startRow = Math.min(lastClickedRowRef.current, currentRow);
        const endRow = Math.max(lastClickedRowRef.current, currentRow);

        console.log(`✅ Shift-click: selecting rows ${startRow} to ${endRow}`);

        // Определяем, выделяем или снимаем выделение
        const shouldSelect = !checkbox.checked;

        // Собираем ID для выделения
        const rangeIds = [];
        for (let i = startRow; i <= endRow; i++) {
          if (tableData[i]) {
            rangeIds.push(tableData[i].id);
          }
        }

        let newSelectedIds;
        if (shouldSelect) {
          // Добавляем все ID из диапазона
          newSelectedIds = [...new Set([...selectedIds, ...rangeIds])];
        } else {
          // Убираем все ID из диапазона
          newSelectedIds = selectedIds.filter(id => !rangeIds.includes(id));
        }

        // Обновляем состояние
        onSelectionChange(newSelectedIds);

        // Обновляем чекбоксы в таблице
        const newData = tableData.map((row, idx) => {
          if (idx >= startRow && idx <= endRow) {
            return { ...row, selected: shouldSelect };
          }
          return row;
        });
        
        instance.loadData(newData);
        
        return;
      }

      // Сохраняем последний кликнутый ряд
      lastClickedRowRef.current = currentRow;
    };

    const tableElement = instance.rootElement;
    tableElement.addEventListener('mousedown', handleMouseDown, true);

    return () => {
      tableElement.removeEventListener('mousedown', handleMouseDown, true);
    };
  }, [tableData, selectedIds, onSelectionChange]);

  // ✅ Рендерер для ссылки "Открыть сайт"
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

  const columns = [
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
          afterColumnResize={handleAfterColumnResize}
          contextMenu={false}
          selectionMode="range"
          outsideClickDeselects={false}
          fillHandle={false}
          columnSorting={true}
          className="keywords-handsontable"
        />
      )}
    </div>
  );
};

export default CompetitorsTable;