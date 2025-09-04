// src/components/Header.jsx
import React from 'react';
import { FaUpload, FaSync, FaCog } from 'react-icons/fa';
import logo from '../assets/logo.png';

const Header = ({ onSettingsClick, onSyncClick, onGoogleAdsClick }) => {
  return (
    <header className="app-header">
      <div className="logo">
        <img src={logo} alt="Ключик, замочек" className="logo-image" />
      </div>
      <div className="header-actions">
        <button className="header-btn" onClick={onGoogleAdsClick} title="Выгрузка в Google Ads">
          <FaUpload />
        </button>
        <button className="header-btn" onClick={onSyncClick} title="Синхронизация с БД">
          <FaSync />
        </button>
        <button className="header-btn" onClick={onSettingsClick} title="Настройки">
          <FaCog />
        </button>
      </div>
    </header>
  );
};

export default Header;