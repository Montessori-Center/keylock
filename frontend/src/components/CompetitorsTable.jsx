// frontend/src/components/CompetitorsTable.jsx
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
        notes: comp.notes || '',
        is_new: comp.is_new || false  // ✅ НОВОЕ: флаг новой школы
      }));
      setTableData(data);
    } else {
      setTableData([]);
    }
  }, [competitors, selectedIds]);

  // ✅ НОВОЕ: Применение стилей для новых записей
  useEffect(() => {
    if (!hotTableRef.current?.hotInstance || tableData.length === 0) return;
    
    const instance = hotTableRef.current.hotInstance;
    
    instance.updateSettings({
      cells: function(row) {
        const cellProperties = {};
        const rowData = this.instance.getSourceDataAtRow(row);
        
        // ✅ Подсветка новых школ
        if (rowData && rowData.is_new) {
          cellProperties.className = 'new-competitor-row';
        }
        
        return cellProperties;
      }
    });
    
    instance.render();
  }, [tableData]);

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
      onSelectionChange(newSelectedIds);
    }
  };

  const handleAfterChange = (changes, source) => {
    if (!changes || source === 'loadData') return;
    
    const hot = hotTableRef.current?.hotInstance;
    if (!hot) return;

    changes.forEach(([row, prop, oldValue, newValue]) => {
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
        onDataChange(id, prop, newValue);
      }
    });
  };

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

  // ✅ ИСПРАВЛЕНО: Рендер кнопки "Открыть сайт"
  function openSiteRenderer(instance, td, row, col, prop, value, cellProperties) {
    Handsontable.renderers.TextRenderer.apply(this, arguments);
    
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
      
      // ✅ КРИТИЧНО: Останавливаем всплытие события
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
          columnSorting={true}
          className="keywords-handsontable"
        />
      )}
    </div>
  );
};

export default CompetitorsTable;
